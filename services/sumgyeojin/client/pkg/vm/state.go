package vm

import (
	"io"
)

type State interface {
	GetOperation(io.Reader) (Operation, error)
	R() IRegister
	J() IRegister
	Q() IRegister
	L() IRegister
	Sufferer() IRegister
	OFD() IRegister
	O() SRegister
	T() SRegister
	D() SRegister
	Linear() IRegister
	Frame() IRegister
	Skek() []int64
}

type state struct {
	r, j, q, l    IRegister
	sufferer, ofd IRegister
	o, t, d       SRegister
	linear, frame IRegister
	skek          []int64
}

func (s *state) GetOperation(r io.Reader) (Operation, error) {
	return getOperation(s, r)
}

func (s *state) R() IRegister {
	return s.r
}

func (s *state) J() IRegister {
	return s.j
}

func (s *state) Q() IRegister {
	return s.q
}

func (s *state) L() IRegister {
	return s.l
}

func (s *state) Sufferer() IRegister {
	return s.sufferer
}

func (s *state) OFD() IRegister {
	return s.ofd
}

func (s *state) O() SRegister {
	return s.o
}

func (s *state) T() SRegister {
	return s.t
}

func (s *state) D() SRegister {
	return s.d
}

func (s *state) Linear() IRegister {
	return s.linear
}

func (s *state) Skek() []int64 {
	return s.skek
}

func (s *state) Frame() IRegister {
	return s.frame
}

const (
	SkekSize = 1024
)

func newState() State {
	return &state{
		r:        &iregister{mapping: "r8", mappingByte: "r8b"},
		j:        &iregister{mapping: "r9", mappingByte: "r9b"},
		q:        &iregister{mapping: "r10", mappingByte: "r10b"},
		l:        &iregister{mapping: "r11", mappingByte: "r11b"},
		sufferer: &iregister{mapping: "r12", mappingByte: "r12b"},
		ofd:      &iregister{mapping: "r13", mappingByte: "r13b", value: -1},
		o:        &sregister{mapping: "r14"},
		t:        &sregister{mapping: "r15"},
		d:        &sregister{mapping: "rbp"},
		linear:   &iregister{mapping: "rbx", mappingByte: "bl"},
		frame:    &iregister{mapping: "rcx", mappingByte: "cl"},
		skek:     make([]int64, SkekSize),
	}
}
