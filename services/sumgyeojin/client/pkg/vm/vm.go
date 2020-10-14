package vm

import (
	"bytes"
	"errors"
	"fmt"
	"io"
	"reflect"
	"sumgyeojin/pkg/jit"
	"syscall"
	"unsafe"
)

type VM interface {
	State() State
	Run(bc []byte) error
}

type vm struct {
	state State
}

func (v *vm) State() State {
	return v.state
}

func (v *vm) dumpStrings() (uintptr, uintptr, uintptr, error) {
	dumpString := func(s []byte) (uintptr, error) {
		mem, err := syscall.Mmap(
			-1,
			0,
			16+cap(s),
			syscall.PROT_READ|syscall.PROT_WRITE,
			syscall.MAP_PRIVATE|syscall.MAP_ANONYMOUS,
		)

		if err != nil {
			return 0, err
		}

		*(*uint64)(unsafe.Pointer(&mem[0])) = uint64(cap(s))
		*(*uint64)(unsafe.Pointer(&mem[8])) = uint64(len(s))
		copy(mem[16:], s)

		return uintptr(unsafe.Pointer(&mem[0])), nil
	}

	o, err := dumpString(v.state.O().Value())
	if err != nil {
		return 0, 0, 0, err
	}

	t, err := dumpString(v.state.T().Value())
	if err != nil {
		return 0, 0, 0, err
	}

	d, err := dumpString(v.state.D().Value())
	if err != nil {
		return 0, 0, 0, err
	}

	return o, t, d, nil
}

func (v *vm) loadStrings(o, t, d uintptr) error {
	loadString := func(s uintptr) []byte {
		c := *(*uint64)(unsafe.Pointer(s))
		l := *(*uint64)(unsafe.Pointer(s + 8))
		sl := make([]byte, l, c)
		for i := uint64(0); i < l; i++ {
			sl[i] = *(*byte)(unsafe.Pointer(s + 16 + uintptr(i)))
		}

		return sl
	}

	unmap := func(s uintptr, c uint64) {
		osl := &reflect.SliceHeader{
			Data: s,
			Len:  int(16 + c),
			Cap:  int(16 + c),
		}
		syscall.Munmap(*(*[]byte)(unsafe.Pointer(osl)))
	}

	ov := loadString(o)
	v.State().O().Set(ov)

	tv := loadString(t)
	v.State().T().Set(tv)

	dv := loadString(d)
	v.State().D().Set(dv)

	oc := *(*uint64)(unsafe.Pointer(o))
	tc := *(*uint64)(unsafe.Pointer(t))
	dc := *(*uint64)(unsafe.Pointer(d))

	unmap(o, oc)
	unmap(t, tc)
	unmap(d, dc)

	return nil
}

const threshold = 20

func (v *vm) Run(bc []byte) error {

	prefix, err := jit.Code(fmt.Sprintf(`
		mov %[1]s, QWORD [rsp+8]
		mov %[2]s, QWORD [rsp+16]
		mov %[3]s, QWORD [rsp+24]
		mov %[4]s, QWORD [rsp+32]
		mov %[5]s, QWORD [rsp+40]
		mov %[6]s, QWORD [rsp+48]
		mov %[7]s, QWORD [rsp+56]
		mov %[8]s, QWORD [rsp+64]
		mov %[9]s, QWORD [rsp+72]
		mov %[10]s, QWORD [rsp+80]
		mov %[11]s, QWORD [rsp+88]
	`,
		v.State().R().ASMRegister(),
		v.State().J().ASMRegister(),
		v.State().Q().ASMRegister(),
		v.State().L().ASMRegister(),
		v.State().Sufferer().ASMRegister(),
		v.State().OFD().ASMRegister(),
		v.State().Linear().ASMRegister(),
		v.State().Frame().ASMRegister(),
		v.State().O().ASMRegister(),
		v.State().T().ASMRegister(),
		v.State().D().ASMRegister()))

	if err != nil {
		return err
	}

	suffix, err := jit.Code(fmt.Sprintf(`
		mov QWORD [rsp+96], %[1]s
		mov QWORD [rsp+104], %[2]s
		mov QWORD [rsp+112], %[3]s
		mov QWORD [rsp+120], %[4]s
		mov QWORD [rsp+128], %[5]s
		mov QWORD [rsp+136], %[6]s
		mov QWORD [rsp+144], %[7]s
		mov QWORD [rsp+152], %[8]s
		mov QWORD [rsp+160], %[9]s
		mov QWORD [rsp+168], %[10]s
		mov QWORD [rsp+176], %[11]s
		ret
	`,
		v.State().R().ASMRegister(),
		v.State().J().ASMRegister(),
		v.State().Q().ASMRegister(),
		v.State().L().ASMRegister(),
		v.State().Sufferer().ASMRegister(),
		v.State().OFD().ASMRegister(),
		v.State().Linear().ASMRegister(),
		v.State().Frame().ASMRegister(),
		v.State().O().ASMRegister(),
		v.State().T().ASMRegister(),
		v.State().D().ASMRegister()))

	if err != nil {
		return err
	}

	frames := make([][]byte, 0)
	var frame []byte

	for i, b := range bc {
		if b != '#' {
			frame = append(frame, b)
		}

		if b == '#' || i+1 == len(bc) {
			frames = append(frames, frame)
			frame = nil
		}
	}

	temperature := make([]int, len(frames))

	for {
		if 0 <= v.State().Frame().Value() && v.State().Frame().Value() < int64(len(frames)) {
			frame = frames[v.State().Frame().Value()]
		} else {
			return errors.New("Invalid frame")
		}

		temperature[v.State().Frame().Value()] += 1

		if v.State().Sufferer().Value() < 0 {
			return errors.New("invalid sufferer")
		}

		if v.State().Sufferer().Value() >= int64(len(frame)) {
			break
		}

		r := bytes.NewReader(frame[v.State().Sufferer().Value():])

		var (
			err  error
			o    Operation
			last bool
		)

		if temperature[v.State().Frame().Value()] >= threshold {
			var jitCode []byte

			for {
				o, err = v.State().GetOperation(r)
				if err != nil {
					if err == io.EOF {
						last = true
						break
					} else {
						return err
					}
				}

				jit, err := o.JIT(v.State())
				if err != nil {
					if err == ErrUnjittableOperation {
						break
					} else {
						return err
					}
				} else {
					jitCode = append(jitCode, jit...)
					o = nil
				}
			}

			jitCode = append(prefix, jitCode...)
			jitCode = append(jitCode, suffix...)

			jitMemory, err := syscall.Mmap(
				-1,
				0,
				len(jitCode),
				syscall.PROT_READ|syscall.PROT_WRITE|syscall.PROT_EXEC,
				syscall.MAP_PRIVATE|syscall.MAP_ANONYMOUS,
			)

			if err != nil {
				return err
			}
			defer func() {
				syscall.Munmap(jitMemory)
			}()

			copy(jitMemory, jitCode)

			helper1 := uintptr(unsafe.Pointer(&jitMemory[0]))
			helper2 := uintptr(unsafe.Pointer(&helper1))
			jitFunc := *(*func(int64, int64, int64, int64, int64, int64, int64, int64, uintptr, uintptr, uintptr) (int64, int64, int64, int64, int64, int64, int64, int64, uintptr, uintptr, uintptr))(unsafe.Pointer(&helper2))

			o, t, d, err := v.dumpStrings()
			if err != nil {
				return err
			}

			r, j, q, l, suf, ofd, lin, fra, on, tn, dn := jitFunc(
				v.State().R().Value(),
				v.State().J().Value(),
				v.State().Q().Value(),
				v.State().L().Value(),
				v.State().Sufferer().Value(),
				v.State().OFD().Value(),
				v.State().Linear().Value(),
				v.State().Frame().Value(),
				o, t, d,
			)

			v.State().R().Set(r)
			v.State().J().Set(j)
			v.State().Q().Set(q)
			v.State().L().Set(l)
			v.State().Sufferer().Set(suf)
			v.State().OFD().Set(ofd)
			v.State().Linear().Set(lin)
			v.State().Frame().Set(fra)
			if err := v.loadStrings(on, tn, dn); err != nil {
				return err
			}
		} else {
			if o, err = v.State().GetOperation(r); err != nil {
				if err == io.EOF {
					last = true
				} else {
					return err
				}
			}
		}

		if o != nil {
			if err := o.Apply(v.State()); err != nil {
				return err
			}
		}

		if last {
			return nil
		}
	}

	return nil
}

func New() VM {
	return &vm{
		state: newState(),
	}
}
