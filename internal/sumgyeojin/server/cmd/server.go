package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/boltdb/bolt"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

type BytecodeForm struct {
	Bytecode string `json:"bytecode`
}

func main() {
	db, err := bolt.Open("./storage/db.db", 0600, nil)
	if err != nil {
		log.Fatalf("Error opening db: %v", err)
	}
	defer db.Close()

	db.Update(func(tx *bolt.Tx) error {
		_, err := tx.CreateBucketIfNotExists([]byte("bytecodes"))
		return err
	})

	gin.SetMode(gin.ReleaseMode)
	r := gin.Default()

	r.POST("/", func(c *gin.Context) {
		var bc BytecodeForm

		if c.BindJSON(&bc) != nil {
			return
		}

		id := uuid.New().String()

		if err := db.Update(func(tx *bolt.Tx) error {
			return tx.Bucket([]byte("bytecodes")).Put([]byte(id), []byte(bc.Bytecode))
		}); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "can't put bytecode in db"})
		} else {
			c.JSON(http.StatusOK, gin.H{"result": id})
		}
	})

	r.GET("/:id", func(c *gin.Context) {
		if err := db.View(func(tx *bolt.Tx) error {
			if bc := tx.Bucket([]byte("bytecodes")).Get([]byte(c.Param("id"))); bc != nil {
				c.JSON(http.StatusOK, gin.H{"result": string(bc)})
			} else {
				c.JSON(http.StatusBadRequest, gin.H{"error": "no such bytecode"})
			}

			return nil
		}); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "can't get bytecode from db"})
		}
	})

	srv := &http.Server{
		Addr:    "0.0.0.0:8080",
		Handler: r,
	}

	go func() {
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Error serving server: %v", err)
		}
	}()

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	log.Println("Shutting down server...")

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := srv.Shutdown(ctx); err != nil {
		log.Fatalf("Server forced to shutdown: %v", err)
	}
}
