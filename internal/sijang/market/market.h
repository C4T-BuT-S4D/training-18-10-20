#include <netinet/in.h>
#include <pthread.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>

typedef int SOCKET;
typedef unsigned long long int QWORD;
typedef unsigned int DWORD;
typedef unsigned short int WORD;
typedef unsigned char BYTE;

typedef struct pthread_args {
	SOCKET client_fd;
} thread_args;


#define USERNAME_SIZE 16
#define PASSWORD_SIZE 16
#define DESCRIPTION_SIZE 40

// 128 + 45 = 173  bytes
typedef struct s_item {
	char name[ 32 ];
	char description[ DESCRIPTION_SIZE ];
	DWORD cost;
	DWORD quality;
	char owner[ USERNAME_SIZE ];
	BYTE is_archived;
	DWORD token;
	char password[ PASSWORD_SIZE ];
	BYTE used;
} market_item;

#define MARKET_MAX_SIZE 64 * 1024 * 1024 // 64 Mbytes
#define MAX_ITEMS_COUNT ( MARKET_MAX_SIZE / sizeof( market_item ) ) - sizeof( QWORD ) * 4 

typedef struct s_market_header {
	QWORD count_of_items;
	QWORD max_item_id;
	market_item chunks[ MAX_ITEMS_COUNT ];
} market_header;

#define ERROR_SOCKET_CREATE 0x01
#define ERROR_SOCKET_BIND   0x02
#define ERROR_SOCKET_LISTEN 0x04

#define FALSE 0 
#define TRUE 1

#define MARKET_PORT 9999
#define LISTEN_CNT 32
#define RECV_TIMEOUT 1
#define REQ_TO_ADD_PACKET_SIZE 256
#define MARKET_ITEM_SIZE 256
#define ACCESS_PACKET_SIZE 6
#define BUSY_PACKET_SIZE 4

#define MARKET_MAPPING_ERROR 0x1001
#define MARKET_OPEN_ERROR 0x1002 

#define MARKET_PATH "./market.db"
#define MARKET_BASE_ADDR 0x44000000

// 0x44000000 - 0x48000000 -- market scope

#define MARKET_ITEM_STRUCT_SIZE sizeof( market_item )

#define MISSING_CMD_TYPE 0x1111
#define NO_FREE_SPACE 0x1112
#define SENDING_ERROR 0x1113
#define ITEM_NOT_FOUND 0x1114
#define ITEM_ACCESS_DENIED 0x1115
#define MARKET_IS_EMPTY 0x1116

#define ITEM_ADDED 0x2221

enum COMMANDS { ADD_ITEM, DEL_ITEM, VIEW_ITEMS, 
	CHANGE_STATUS, FULL_ITEM_INFO, UPDATE_ITEM,
	GET_PAGE, ITEM_INFO, UNDEF_CMD };

void setup( void );
void *pthread_routine( void* );
int market_init( void );
int proceed_packet( enum COMMANDS, char*, int );
enum COMMANDS get_cmd_by_name( char* );
int find_free_entry( void );

int add_item( char* packet, int client_fd );
int del_item( char* packet, int client_fd );
int view_items( char* packet );
int change_status( char* packet );
int full_item_info( char* packet, int client_fd ); 
market_item* find_item_by_token( DWORD token );

void page_not_found( int client_fd );
void market_is_empty( int client_fd );
void item_updated( int client_fd );
void access_denied( int client_fd );
void item_not_found( int client_fd );
int get_page( char* packet, int client_fd );
int update_item( char* packet, int client_fd );
int item_info( char* packet, int client_fd );
void send_item_info( int client_fd, market_item* item );
void send_full_item_info( market_item* item, int client_fd );
int find_item_idx_by_token( DWORD token );

market_header* g_market;



// add item req packet
// magic|<item-name>|<description>|<cost>|<quality>|<owner>|<archived>|<token>|<password>
// 
// full_item_info
// magic|<item-token>|username|password|
// 
// get_page
// magic|<page-number>|<count on one page>|
// 