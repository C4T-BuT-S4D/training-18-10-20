package vm

import (
	"errors"
	"fmt"
	"io"
	"sumgyeojin/pkg/jit"
	"syscall"
	"unsafe"
)

var ErrUnjittableOperation = errors.New("operation can't be jitted")

type Operation interface {
	Apply(s State) error
	JIT(s State) ([]byte, error)
}

func getOperation(s State, r io.Reader) (Operation, error) {
	roc := make([]byte, 1)
	if _, err := r.Read(roc); err != nil {
		return nil, err
	}
	s.Sufferer().Set(s.Sufferer().Value() + 1)

	switch roc[0] {
	case '0':
		return &oReset{}, nil
	case '?':
		return &oInfo{}, nil
	case '!':
		target, err := getSOperands(s, r, 1)
		if err != nil {
			return nil, err
		}

		return &oPrint{
			target: target[0],
		}, nil
	case 'm':
		ops, err := getIOperands(s, r, 2)
		if err != nil {
			return nil, err
		}

		return &oIMov{
			from: ops[1],
			to:   ops[0],
		}, nil
	case 'M':
		ops, err := getSOperands(s, r, 2)
		if err != nil {
			return nil, err
		}

		return &oSMov{
			from: ops[1],
			to:   ops[0],
		}, nil
	case 'B':
		ops, err := getIOperands(s, r, 1)
		if err != nil {
			return nil, err
		}

		return &oStackFrame{
			target: ops[0],
		}, nil
	case 'i':
		ops, err := getIOperands(s, r, 1)
		if err != nil {
			return nil, err
		}

		return &oInc{
			target: ops[0],
		}, nil
	case 'd':
		ops, err := getIOperands(s, r, 1)
		if err != nil {
			return nil, err
		}

		return &oDec{
			target: ops[0],
		}, nil
	case 'a':
		to, err := getSOperands(s, r, 1)
		if err != nil {
			return nil, err
		}

		from, err := getIOperands(s, r, 1)
		if err != nil {
			return nil, err
		}

		return &oAppend{
			from: from[0],
			to:   to[0],
		}, nil
	case '+':
		ops, err := getIOperands(s, r, 2)
		if err != nil {
			return nil, err
		}

		return &oAdd{
			from: ops[1],
			to:   ops[0],
		}, nil
	case '-':
		ops, err := getIOperands(s, r, 2)
		if err != nil {
			return nil, err
		}

		return &oSub{
			from: ops[1],
			to:   ops[0],
		}, nil
	case '*':
		ops, err := getIOperands(s, r, 2)
		if err != nil {
			return nil, err
		}

		return &oMul{
			from: ops[1],
			to:   ops[0],
		}, nil
	case '/':
		ops, err := getIOperands(s, r, 2)
		if err != nil {
			return nil, err
		}

		return &oDiv{
			from: ops[1],
			to:   ops[0],
		}, nil
	case '&':
		ops, err := getIOperands(s, r, 2)
		if err != nil {
			return nil, err
		}

		return &oAnd{
			from: ops[1],
			to:   ops[0],
		}, nil
	case '|':
		ops, err := getIOperands(s, r, 2)
		if err != nil {
			return nil, err
		}

		return &oOr{
			from: ops[1],
			to:   ops[0],
		}, nil
	case '^':
		ops, err := getIOperands(s, r, 2)
		if err != nil {
			return nil, err
		}

		return &oXor{
			from: ops[1],
			to:   ops[0],
		}, nil
	case '~':
		ops, err := getIOperands(s, r, 1)
		if err != nil {
			return nil, err
		}

		return &oNot{
			target: ops[0],
		}, nil
	case 'o':
		filename, err := getSOperands(s, r, 1)
		if err != nil {
			return nil, err
		}

		rmode := make([]byte, 1)
		if _, err := r.Read(rmode); err != nil {
			return nil, err
		}
		s.Sufferer().Set(s.Sufferer().Value() + 1)

		return &oOpen{
			filename: filename[0],
			t:        rmode[0],
		}, nil
	case 'r':
		to, err := getSOperands(s, r, 1)
		if err != nil {
			return nil, err
		}

		cnt, err := getIOperands(s, r, 1)
		if err != nil {
			return nil, err
		}

		return &oFileRead{
			to:  to[0],
			cnt: cnt[0],
		}, nil
	case 'w':
		from, err := getSOperands(s, r, 1)
		if err != nil {
			return nil, err
		}

		return &oFileWrite{
			from: from[0],
		}, nil
	case 'p':
		ops, err := getIOperands(s, r, 1)
		if err != nil {
			return nil, err
		}

		return &oPush{
			target: ops[0],
		}, nil
	case 'P':
		ops, err := getIOperands(s, r, 1)
		if err != nil {
			return nil, err
		}

		return &oPop{
			target: ops[0],
		}, nil
	case 'c':
		ops, err := getIOperands(s, r, 1)
		if err != nil {
			return nil, err
		}

		return &oCall{
			target: ops[0],
		}, nil
	case 'j':
		ops, err := getIOperands(s, r, 1)
		if err != nil {
			return nil, err
		}

		return &oJmp{
			target: ops[0],
		}, nil
	case 'J':
		ops, err := getIOperands(s, r, 3)
		if err != nil {
			return nil, err
		}

		return &oJlt{
			l:      ops[0],
			r:      ops[1],
			target: ops[2],
		}, nil
	}

	return nil, errors.New("invalid operation")
}

func getIOperands(s State, r io.Reader, num int) ([]IRegister, error) {
	operands := make([]IRegister, num)
	for i := 0; i < num; i++ {
		rop := make([]byte, 1)
		if _, err := r.Read(rop); err != nil {
			return nil, errors.New("not enough operands")
		}
		s.Sufferer().Set(s.Sufferer().Value() + 1)

		var op IRegister

		switch rop[0] {
		case 'r':
			op = s.R()
		case 'j':
			op = s.J()
		case 'q':
			op = s.Q()
		case 'l':
			op = s.L()
		case 's':
			op = s.Sufferer()
		case 'o':
			op = s.OFD()
		case 'L':
			op = s.Linear()
		default:
			return nil, errors.New("invalid operand")
		}

		operands[i] = op
	}

	return operands, nil
}

func getSOperands(s State, r io.Reader, num int) ([]SRegister, error) {
	operands := make([]SRegister, num)
	for i := 0; i < num; i++ {
		rop := make([]byte, 1)
		if _, err := r.Read(rop); err != nil {
			return nil, err
		}
		s.Sufferer().Set(s.Sufferer().Value() + 1)

		var op SRegister

		switch rop[0] {
		case 'o':
			op = s.O()
		case 't':
			op = s.T()
		case 'd':
			op = s.D()
		default:
			return nil, errors.New("invalid operand")
		}

		operands[i] = op
	}

	return operands, nil
}

type oReset struct{}

func (o *oReset) Apply(s State) error {
	s.R().Set(0)
	s.J().Set(0)
	s.Q().Set(0)
	s.L().Set(0)
	s.OFD().Set(0)
	s.O().Set([]byte{})
	s.T().Set([]byte{})
	s.D().Set([]byte{})
	s.Linear().Set(0)
	return nil
}

func (o *oReset) JIT(s State) ([]byte, error) {
	return jit.Code(fmt.Sprintf(`
		xor %[1]s, %[1]s
		xor %[2]s, %[2]s
		xor %[3]s, %[3]s
		xor %[4]s, %[4]s
		xor %[5]s, %[5]s
		mov QWORD [%[6]s + 8], 0
		mov QWORD [%[7]s + 8], 0
		mov QWORD [%[8]s + 8], 0
	`,
		s.R().ASMRegister(),
		s.J().ASMRegister(),
		s.Q().ASMRegister(),
		s.L().ASMRegister(),
		s.Linear().ASMRegister(),
		s.O().ASMRegister(),
		s.T().ASMRegister(),
		s.D().ASMRegister()))
}

type oInfo struct{}

func (o *oInfo) Apply(s State) error {
	fmt.Printf("R: %d\n", s.R().Value())
	fmt.Printf("J: %d\n", s.J().Value())
	fmt.Printf("Q: %d\n", s.Q().Value())
	fmt.Printf("L: %d\n", s.L().Value())
	fmt.Printf("Sufferer: %d\n", s.Sufferer().Value())
	fmt.Printf("OFD: %d\n", s.OFD().Value())
	fmt.Printf("O: %v\n", s.O().Value())
	fmt.Printf("T: %v\n", s.T().Value())
	fmt.Printf("D: %v\n", s.D().Value())
	fmt.Printf("Linear: %d\n", s.Linear().Value())
	fmt.Printf("Frame: %d\n", s.Frame().Value())
	fmt.Printf("Skek: %v\n", s.Skek())
	return nil
}

func (o *oInfo) JIT(s State) ([]byte, error) {
	return nil, ErrUnjittableOperation
}

type oPrint struct {
	target SRegister
}

func (o *oPrint) Apply(s State) error {
	fmt.Print(string(o.target.Value()))
	return nil
}

func (o *oPrint) JIT(s State) ([]byte, error) {
	return jit.Code(fmt.Sprintf(`
		xor rax, rax
		inc rax
		xor rdi, rdi
		inc rdi
		mov rsi, %[1]s
		add rsi, 16
		mov rdx, QWORD [%[1]s + 8]
		push rcx
		push r11
		syscall
		pop r11
		pop rcx
	`, o.target.ASMRegister()))
}

type oIMov struct {
	from IRegister
	to   IRegister
}

func (o *oIMov) Apply(s State) error {
	o.to.Set(o.from.Value())
	return nil
}

func (o *oIMov) JIT(s State) ([]byte, error) {
	return jit.Code(fmt.Sprintf(`
		mov %[1]s, %[2]s
	`,
		o.to.ASMRegister(),
		o.from.ASMRegister()))
}

type oSMov struct {
	from SRegister
	to   SRegister
}

func (o *oSMov) Apply(s State) error {
	o.to.Set(o.from.Value())
	return nil
}

func (o *oSMov) JIT(s State) ([]byte, error) {
	return jit.Code(fmt.Sprintf(`
		xor rdi, rdi
		mov rsi, QWORD [%[2]s]
		add rsi, 16
		mov rdx, 3
		push r10
		mov r10, 34
		push r8
		xor r8, r8
		dec r8
		push r9
		xor r9, r9
		push rcx
		push r11
		mov rax, 9
		syscall
		pop r11
		pop rcx
		pop r9
		pop r8
		pop r10

		mov rdi, rax

		push rdi

		mov rax, QWORD [%[2]s]
		mov QWORD [rdi], rax
		mov rax, QWORD [%[2]s + 8]
		mov QWORD [rdi + 8], rax

		add rdi, 16
		mov rax, QWORD [%[2]s + 8]
		mov rsi, %[2]s
		add rsi, 16

	COPY:
		test rax, rax
		jz ENDCP
		dec rax
		mov dl, BYTE [rsi]
		mov BYTE [rdi], dl
		inc rdi
		inc rsi
		jmp COPY
	ENDCP:
		mov rdi, %[1]s
		mov rsi, QWORD [%[1]s]
		mov rax, 11
		push rcx
		push r11
		syscall
		pop r11
		pop rcx

		pop %[1]s
	`,
		o.to.ASMRegister(),
		o.from.ASMRegister()))
}

type oStackFrame struct {
	target IRegister
}

func (o *oStackFrame) Apply(s State) error {
	o.target.Set(int64(uintptr(unsafe.Pointer(&s.Skek()[0]))))
	return nil
}

func (o *oStackFrame) JIT(s State) ([]byte, error) {
	return nil, ErrUnjittableOperation
}

type oInc struct {
	target IRegister
}

func (o *oInc) Apply(s State) error {
	o.target.Set(o.target.Value() + 1)
	return nil
}

func (o *oInc) JIT(s State) ([]byte, error) {
	return jit.Code(fmt.Sprintf(`
		inc %[1]s
	`,
		o.target.ASMRegister()))
}

type oDec struct {
	target IRegister
}

func (o *oDec) Apply(s State) error {
	o.target.Set(o.target.Value() - 1)
	return nil
}

func (o *oDec) JIT(s State) ([]byte, error) {
	return jit.Code(fmt.Sprintf(`
		dec %[1]s
	`,
		o.target.ASMRegister()))
}

type oAppend struct {
	from IRegister
	to   SRegister
}

func (o *oAppend) Apply(s State) error {
	o.to.Set(append(o.to.Value(), byte((o.from.Value()%256+256)%256)))
	return nil
}

func (o *oAppend) JIT(s State) ([]byte, error) {
	return jit.Code(fmt.Sprintf(`
		mov rax, QWORD [%[1]s]
		mov rdi, QWORD [%[1]s + 8]
		cmp rax, rdi
		jnz SKP
	REALLOC:
		inc rax
		shl rax, 1
		push rax
		push rdi

		xor rdi, rdi
		mov rsi, rax
		mov rdx, 3
		push r10
		mov r10, 34
		push r8
		xor r8, r8
		dec r8
		push r9
		xor r9, r9
		mov rax, 9
		push rcx
		push r11
		syscall
		pop r11
		pop rcx
		mov rdx, rax
		pop r9
		pop r8
		pop r10

		push rdx
		mov rax, QWORD [%[1]s + 8]
		mov rdi, rdx
		add rdi, 16
		mov rsi, %[1]s
		add rsi, 16
	COPY:
		test rax, rax
		jz ENDCP
		dec rax
		mov dl, BYTE [rsi]
		mov BYTE [rdi], dl
		inc rdi
		inc rsi
		jmp COPY
	ENDCP:
		pop rdx
		mov rax, 11
		mov rdi, %[1]s
		mov rsi, QWORD [%[1]s]
		push rcx
		push r11
		syscall
		pop r11
		pop rcx

		mov %[1]s, rdx

		pop rdi
		mov QWORD [%[1]s + 8], rdi
		pop rax
		mov QWORD [%[1]s], rax
	SKP:
		add rdi, %[1]s
		add rdi, 16
		mov BYTE [rdi], %[2]s
		inc QWORD [%[1]s + 8]
	`,
		o.to.ASMRegister(),
		o.from.ASMRegisterByte()))
}

type oAdd struct {
	from IRegister
	to   IRegister
}

func (o *oAdd) Apply(s State) error {
	o.to.Set(o.to.Value() + o.from.Value())
	return nil
}

func (o *oAdd) JIT(s State) ([]byte, error) {
	return jit.Code(fmt.Sprintf(`
		add %[1]s, %[2]s
	`,
		o.to.ASMRegister(),
		o.from.ASMRegister()))
}

type oSub struct {
	from IRegister
	to   IRegister
}

func (o *oSub) Apply(s State) error {
	o.to.Set(o.to.Value() - o.from.Value())
	return nil
}

func (o *oSub) JIT(s State) ([]byte, error) {
	return jit.Code(fmt.Sprintf(`
		sub %[1]s, %[2]s
	`,
		o.to.ASMRegister(),
		o.from.ASMRegister()))
}

type oMul struct {
	from IRegister
	to   IRegister
}

func (o *oMul) Apply(s State) error {
	o.to.Set(o.to.Value() * o.from.Value())
	return nil
}

func (o *oMul) JIT(s State) ([]byte, error) {
	return jit.Code(fmt.Sprintf(`
		imul %[1]s, %[2]s
	`,
		o.to.ASMRegister(),
		o.from.ASMRegister()))
}

type oDiv struct {
	from IRegister
	to   IRegister
}

func (o *oDiv) Apply(s State) error {
	o.to.Set(o.to.Value() / o.from.Value())
	return nil
}

func (o *oDiv) JIT(s State) ([]byte, error) {
	return jit.Code(fmt.Sprintf(`
		xor rdx, rdx
		mov rax, %[1]s
		cqo
		idiv %[2]s
		mov %[1]s, rax
	`,
		o.to.ASMRegister(),
		o.from.ASMRegister()))
}

type oAnd struct {
	from IRegister
	to   IRegister
}

func (o *oAnd) Apply(s State) error {
	o.to.Set(o.to.Value() & o.from.Value())
	return nil
}

func (o *oAnd) JIT(s State) ([]byte, error) {
	return jit.Code(fmt.Sprintf(`
		and %[1]s, %[2]s
	`,
		o.to.ASMRegister(),
		o.from.ASMRegister()))
}

type oOr struct {
	from IRegister
	to   IRegister
}

func (o *oOr) Apply(s State) error {
	o.to.Set(o.to.Value() | o.from.Value())
	return nil
}

func (o *oOr) JIT(s State) ([]byte, error) {
	return jit.Code(fmt.Sprintf(`
		or %[1]s, %[2]s
	`,
		o.to.ASMRegister(),
		o.from.ASMRegister()))
}

type oXor struct {
	from IRegister
	to   IRegister
}

func (o *oXor) Apply(s State) error {
	o.to.Set(o.to.Value() ^ o.from.Value())
	return nil
}

func (o *oXor) JIT(s State) ([]byte, error) {
	return jit.Code(fmt.Sprintf(`
		xor %[1]s, %[2]s
	`,
		o.to.ASMRegister(),
		o.from.ASMRegister()))
}

type oNot struct {
	target IRegister
}

func (o *oNot) Apply(s State) error {
	o.target.Set(^o.target.Value())
	return nil
}

func (o *oNot) JIT(s State) ([]byte, error) {
	return jit.Code(fmt.Sprintf(`
		xor %[1]s, 0xffffffffffffffff
	`,
		o.target.ASMRegister()))
}

type oOpen struct {
	filename SRegister
	t        byte
}

func (o *oOpen) Apply(s State) error {
	if s.OFD().Value() != -1 {
		if err := syscall.Close(int(s.OFD().Value())); err != nil {
			return err
		} else {
			s.OFD().Set(-1)
		}
	}

	var (
		fd  int
		err error
	)

	switch o.t {
	case 'r':
		fd, err = syscall.Open(string(o.filename.Value()), syscall.O_RDONLY|syscall.O_CREAT, 0600)
		if err != nil {
			return err
		}
	case 'w':
		fd, err = syscall.Open(string(o.filename.Value()), syscall.O_WRONLY|syscall.O_CREAT|syscall.O_TRUNC, 0600)
		if err != nil {
			return err
		}
	default:
		return errors.New("invalid file mode")
	}

	s.OFD().Set(int64(fd))
	return nil
}

func (o *oOpen) JIT(s State) ([]byte, error) {
	return jit.Code(fmt.Sprintf(`
		cmp %[1]s, -1
		jz OPEN
		mov rdi, %[1]s
		mov rax, 3
		push rcx
		push r11
		syscall
		pop r11
		pop rcx
	OPEN:
		xor rdi, rdi
		mov rsi, QWORD [%[2]s + 8]
		inc rsi
		mov rdx, 3
		push r10
		mov r10, 34
		push r8
		xor r8, r8
		dec r8
		push r9
		xor r9, r9
		push rcx
		push r11
		mov rax, 9
		syscall
		pop r11
		pop rcx
		pop r9
		pop r8
		pop r10

		mov rdi, rax
		mov rax, QWORD [%[2]s + 8]
		mov rsi, %[2]s
		add rsi, 16

		push rdi

	COPY:
		test rax, rax
		jz ENDCP
		dec rax
		mov dl, BYTE [rsi]
		mov BYTE [rdi], dl
		inc rdi
		inc rsi
		jmp COPY
	ENDCP:
		mov BYTE [rdi], 0

		mov al, %[3]d
		cmp al, 114
		jz READ
		cmp al, 119
		jz WRITE
		jmp END
	READ:

		pop rdi
		push rdi

		mov rsi, 64
		mov rdx, 384
		push rcx
		push r11
		mov rax, 2
		syscall
		pop r11
		pop rcx
		mov %[1]s, rax

		jmp END
	WRITE:

		pop rdi
		push rdi

		mov rsi, 577
		mov rdx, 384
		push rcx
		push r11
		mov rax, 2
		syscall
		pop r11
		pop rcx
		mov %[1]s, rax

	END:
		pop rdi
		mov rsi, QWORD [%[2]s + 8]
		inc rsi
		mov rax, 11
		push rcx
		push r11
		syscall
		pop r11
		pop rcx
	`,
		s.OFD().ASMRegister(),
		o.filename.ASMRegister(),
		o.t))
}

type oFileRead struct {
	to  SRegister
	cnt IRegister
}

func (o *oFileRead) Apply(s State) error {
	if s.OFD().Value() == -1 {
		return errors.New("invalid ofd register")
	}

	buf := make([]byte, o.cnt.Value())

	n, err := syscall.Read(int(s.OFD().Value()), buf)
	if err != nil {
		return err
	}

	o.to.Set(buf[:n])

	return nil
}

func (o *oFileRead) JIT(s State) ([]byte, error) {
	return jit.Code(fmt.Sprintf(`
		cmp %[1]s, -1
		jz SKP

		xor rdi, rdi
		mov rsi, %[3]s
		add rsi, 16
		mov rdx, 3
		push r10
		mov r10, 34
		push r8
		xor r8, r8
		dec r8
		push r9
		xor r9, r9
		mov rax, 9
		push rcx
		push r11
		syscall
		pop r11
		pop rcx
		pop r9
		pop r8
		pop r10

		push rax
		mov rsi, rax
		add rsi, 16
		xor rax, rax
		mov rdi, %[1]s
		mov rdx, %[3]s
		push rcx
		push r11
		syscall
		pop r11
		pop rcx

		cmp rax, 0
		jnl OK
		jmp ERR
	OK:
		pop rdi
		mov QWORD [rdi], %[3]s
		mov QWORD [rdi + 8], rax

		push rdi

		mov rax, 11
		mov rdi, %[2]s
		mov rsi, QWORD [rdi]
		push rcx
		push r11
		syscall
		pop r11
		pop rcx

		pop rdi

		mov %[2]s, rdi
		jmp SKP
	ERR:
		pop rdi
		mov rsi, %[3]s
		add rsi, 16
		mov rax, 11
		push rcx
		push r11
		syscall
		pop r11
		pop rcx
	SKP:
	`,
		s.OFD().ASMRegister(),
		o.to.ASMRegister(),
		o.cnt.ASMRegister()))
}

type oFileWrite struct {
	from SRegister
}

func (o *oFileWrite) Apply(s State) error {
	if s.OFD().Value() == -1 {
		return errors.New("invalid ofd register")
	}

	if _, err := syscall.Write(int(s.OFD().Value()), o.from.Value()); err != nil {
		return err
	}

	return nil
}

func (o *oFileWrite) JIT(s State) ([]byte, error) {
	return jit.Code(fmt.Sprintf(`
		cmp %[1]s, -1
		jz SKP

		mov rsi, %[2]s
		add rsi, 16
		mov rdi, %[1]s
		mov rdx, QWORD [%[2]s + 8]
		mov rax, 1
		push rcx
		push r11
		syscall
		pop r11
		pop rcx
	SKP:
	`,
		s.OFD().ASMRegister(),
		o.from.ASMRegister()))
}

type oPush struct {
	target IRegister
}

func (o *oPush) Apply(s State) error {
	if s.Linear().Value() < SkekSize {
		s.Skek()[s.Linear().Value()] = o.target.Value()
		s.Linear().Set(s.Linear().Value() + 1)
	} else {
		return errors.New("stack overflow")
	}

	return nil
}

func (o *oPush) JIT(s State) ([]byte, error) {
	return jit.Code(fmt.Sprintf(`
		cmp %[1]s, %[2]d
		jge SKP
		mov rdi, %[3]d
		mov QWORD [rdi + %[1]s*8], %[4]s
		inc %[1]s
	SKP:
	`,
		s.Linear().ASMRegister(),
		SkekSize,
		&s.Skek()[0],
		o.target.ASMRegister()))
}

type oPop struct {
	target IRegister
}

func (o *oPop) Apply(s State) error {
	if s.Linear().Value() > 0 {
		s.Linear().Set(s.Linear().Value() - 1)
		o.target.Set(s.Skek()[s.Linear().Value()])
	} else {
		return errors.New("stack underflow")
	}

	return nil
}

func (o *oPop) JIT(s State) ([]byte, error) {
	return jit.Code(fmt.Sprintf(`
		cmp %[1]s, 0
		jle SKP
		mov rdi, %[2]d
		dec %[1]s
		mov %[3]s, QWORD [rdi + %[1]s*8]
	SKP:
	`,
		s.Linear().ASMRegister(),
		&s.Skek()[0],
		o.target.ASMRegister()))
}

type oCall struct {
	target IRegister
}

func (o *oCall) Apply(s State) error {
	s.Frame().Set(o.target.Value())
	s.Sufferer().Set(0)
	return nil
}

func (o *oCall) JIT(s State) ([]byte, error) {
	return nil, ErrUnjittableOperation
}

type oJmp struct {
	target IRegister
}

func (o *oJmp) Apply(s State) error {
	s.Sufferer().Set(o.target.Value())
	return nil
}

func (o *oJmp) JIT(s State) ([]byte, error) {
	return nil, ErrUnjittableOperation
}

type oJlt struct {
	l      IRegister
	r      IRegister
	target IRegister
}

func (o *oJlt) Apply(s State) error {
	if o.l.Value() < o.r.Value() {
		s.Sufferer().Set(o.target.Value())
	}
	return nil
}

func (o *oJlt) JIT(s State) ([]byte, error) {
	return nil, ErrUnjittableOperation
}
