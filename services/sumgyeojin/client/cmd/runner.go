package main

import (
	"fmt"
	"os"
	"sumgyeojin/pkg/vm"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Bytecode is not provided")
		return
	}

	v := vm.New()
	if err := v.Run([]byte(os.Args[1])); err != nil {
		fmt.Printf("Error: %v", err)
	}
}
