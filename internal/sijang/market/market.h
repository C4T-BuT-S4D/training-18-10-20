#include <netinet/in.h>
#include <pthread.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>

typedef int SOCKET;

#define ERROR_SOCKET_CREATE 0x01
#define ERROR_SOCKET_BIND   0x02
#define ERROR_SOCKET_LISTEN 0x04


#define MARKET_PORT 9999
#define LISTEN_CNT 32

void setup( void );