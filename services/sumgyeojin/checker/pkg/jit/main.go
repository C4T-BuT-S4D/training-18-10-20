package jit

import (
	"context"
	"fmt"
	"io"
	"io/ioutil"
	"os"
	"os/exec"
	"strings"
	"time"
)

const nasmPrepend = "bits 64\n"

var cache map[string][]byte

func init() {
	cache = make(map[string][]byte)
}

func Code(code string) ([]byte, error) {
	res, ok := cache[code]
	if ok {
		return res, nil
	}

	payload := nasmPrepend + code

	f, err := ioutil.TempFile("", "jit")
	if err != nil {
		return nil, err
	}
	defer os.Remove(f.Name())

	_, err = io.Copy(f, strings.NewReader(payload))
	if err != nil {
		return nil, err
	}

	outName := fmt.Sprintf("%s.out", f.Name())

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	cmd := exec.CommandContext(ctx, "nasm", f.Name(), "-o", outName)
	_, _ = cmd.Output()
	defer os.Remove(outName)

	if ctx.Err() != nil {
		return nil, ctx.Err()
	}

	res, err = ioutil.ReadFile(outName)
	if err == nil {
		cache[code] = res
	}

	return res, err
}
