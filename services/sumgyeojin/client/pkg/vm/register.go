package vm

type IRegister interface {
	ASMRegister() string
	ASMRegisterByte() string
	Value() int64
	Set(int64)
}

type iregister struct {
	mapping     string
	mappingByte string
	value       int64
}

func (r *iregister) ASMRegister() string {
	return r.mapping
}

func (r *iregister) ASMRegisterByte() string {
	return r.mappingByte
}

func (r *iregister) Value() int64 {
	return r.value
}

func (r *iregister) Set(value int64) {
	r.value = value
}

type SRegister interface {
	ASMRegister() string
	Value() []byte
	Set([]byte)
}

type sregister struct {
	mapping string
	value   []byte
}

func (r *sregister) ASMRegister() string {
	return r.mapping
}

func (r *sregister) Value() []byte {
	return r.value
}

func (r *sregister) Set(value []byte) {
	r.value = make([]byte, len(value))
	copy(r.value, value)
}
