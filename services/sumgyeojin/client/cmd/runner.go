package main

import (
	"log"
	"os"
	"sumgyeojin/pkg/vm"
)

func main() {
	if len(os.Args) < 2 {
		log.Fatal("Bytecode is not provided")
		return
	}

	v := vm.New()
	if err := v.Run([]byte(os.Args[1])); err != nil {
		log.Fatalf("Error: %v", err)
	}
}
