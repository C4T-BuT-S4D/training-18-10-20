#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <pthread.h>
#include <time.h>
#include <netinet/in.h>
#include <netdb.h>
#include <malloc.h>
#include <sys/socket.h>  

typedef unsigned long long int QWORD;
typedef unsigned int DWORD;
typedef unsigned short int WORD;
typedef unsigned char BYTE;

// build conditions
//#define MACOS 1
//#define DEBUG 1
#define LINUX 1

// some const
#define DEFAULT_ALARM_TIME 120
#define USERNAME_SIZE 16
#define PASSWORD_SIZE 16
#define FILENAME_SIZE 512
#define DEFUALT_BUF_SIZE 1024
#define DEFAULT_COINS_COUNT 512
#define REQ_TO_ADD_PACKET_SIZE 128
#define DESCRIPTION_SIZE 40
#define MARKET_ITEM_SIZE 256
#define PAGE_SIZE 10
#define WORD_MAX 0xffff
#define MARKET_PORT 9999
#define SLEEP_TIME 200000
#define SLEEP_TRIES 7
#define RECV_TIMEOUT 2

#define FALSE 0 
#define TRUE 1

// Errors
#define INCORRECT_OPTION -1
#define MALLOC_ERROR -2
#define FREE_CHUNK_ERROR -3 
#define FILE_OPEN_TO_WRITE_ERROR -4
#define FILE_OPEN_TO_READ_ERROR -5
#define INVALID_WEAPON_STRUCT -6
#define INVALID_WEAPON_STRING -7
#define SOCKET_CREATE_ERROR -8
#define INVALID_REQUEST_PACKET -9
#define MARKET_SEND_REQ_ERROR -10
#define INVALID_ITEM_POINTER -11
#define MARKET_GET_RECV_ERROR -12
#define MARKET_INTERNRAL_ERROR -13
#define INTERNAL_ERROR -14
#define NOT_ENOUGH_MONEY -15
#define NORMAL_EXIT 0

// options
#define LOGIN 1 
#define REGISTER 2
#define EXIT 3

#define MARKET_HOST_NAME "sijang_market"

enum USER_MENU_OPTIONS { EMPTRY, VIEW_PROFILE, BUY_WEAPON, 
	SELL_WEAPON, CHANGE_STATUS, SET_WEAPON, UNSET_WEAPON, 
	USER_EXIT 
};

enum MARKET_CODES { MARKET_BUSY, MARKET_ACCESS, MARKET_ITEM_ADDED,
	MARKET_ITEM_NOT_ADDED, MARKET_ITEM_NOT_FOUND, MARKET_ITEM_ACCESS_ERR,
	UNDEFINED_RET_CODE, MARKET_ITEM_FULLINFO, MARKET_ITEM_UPDATED, MARKET_PAGE_ITEMS_GETED,
	MARKET_IS_EMPTY, MARKET_ITEM_INFO, MARKET_PAGE_NOT_FOUND, MARKET_ITEM_DELETED
};

// 21 byte
typedef struct {
	char* name; // +0
	QWORD cost; // +8
	DWORD token; // +16
	BYTE id; // +20
} page_item;

typedef struct {
	char* name; // +0
	char* description; // + 8
	DWORD quality; // +16
	BYTE is_seted; // +20
} weapon;

typedef struct {
	char* name;
	char* password;
	DWORD coins;
	weapon** weapons;
	DWORD weapon_count;
	BYTE is_weapon_set;
	weapon* current_weapon;
} user;

typedef struct {
	weapon* wp;
	int m_cost;
	int u_cost;
	char* owner;
	BYTE archive;
} add_to_market_args;

// 37 bytes
typedef struct {
	char* name; // +0
	char* owner; // +8
	char* desc; // +16
	DWORD cost; // +24
	DWORD quality; // +28
	DWORD token; // + 32
	BYTE archive; // +36
} market_item;

// reg login
int init_user( char* );
int login( void );
int reg( void );
void reg_user( char*, char* );
int user_session( void );

void read_password( char*, char* );
int check_password( char*, char* );

// utils
void setup( void );
int read_int( void );
int read_buf( char*, int );
void* alloc_mem( size_t );
void free_mem( void* );
void free_weapon( weapon* );
void sanitize( char* );
char** get_file_lines( char* );
char* get_user_filename( char* );
int find_userfile( char* );
int read_coins( char* );

// rand utils 
BYTE rand8( void );
WORD rand16( void );
DWORD rand32( void );

// menu
void print_menu( void );
void print_user_menu( void );

// user utils
weapon* get_random_weapon( void );
BYTE* weapon2str( weapon* wp );
void parse_weapon_line( weapon* , char* );
void remove_weapon_by_id( int );
int remove_weapon( char*, DWORD );
int save_current_user( void );

void add_weapon( weapon* );

// user menu funcs
void view_profile( void );
void set_weapon( void );
void unset_weapon( void );
int buy_weapon( void );
void sell_weapon( void );

// market functions
int connect_to_market( void );
int close_connection( int );
char* market_item2request( market_item* );
int request_to_add_item( int );
int send_req( int, char* );
void add_to_market_thr( weapon*, int, int, BYTE );
void* add_to_market_hndl( void* args );
int change_weapon_status( void );

enum MARKET_CODES request_full_item_info( DWORD token, market_item* wp );
enum MARKET_CODES request_to_access( char* req_packet, int packet_size, int fd );
enum MARKET_CODES update_item_request( market_item* wp );
enum MARKET_CODES get_items_from_server( int page_id, page_item** );
enum MARKET_CODES request_item_info( DWORD token, market_item* wp );
enum MARKET_CODES buy_item( DWORD token, market_item* itm );
enum MARKET_CODES buy( DWORD token, market_item* item );

int buy_by_token( page_item** page );
int buy_by_page_id( page_item** page );
int get_another_page( page_item** page );


char banner[] =
" _______ __________________ _______  _        _______ \n"\
"(  ____ \\\\__   __/\\__    _/(  ___  )( (    /|(  ____ \\\n"\
"| (    \\/   ) (      )  (  | (   ) ||  \\  ( || (    \\/\n"\
"| (_____    | |      |  |  | (___) ||   \\ | || |      \n"\
"(_____  )   | |      |  |  |  ___  || (\\ \\) || | ____ \n"\
"      ) |   | |      |  |  | (   ) || | \\   || | \\_  )\n"\
"/\\____) |___) (___|\\_)  )  | )   ( || )  \\  || (___) |\n"\
"\\_______)\\_______/(____/   |/     \\||/    )_)(_______)\n"\
"                                                      \n";

char table_header[] = 
"+-----+--+----------------------------+--+----------+--+-------------+\n"\
"|  #  |--|            Name            |--|   Cost   |--|    Token    |\n"\
"+-----+--+----------------------------+--+----------+--+-------------+\n";

char menu[] = 
"Login menu:\n"\
"1. Login\n" \
"2. Register\n"\
"3. Exit";

char user_menu[] = 
"User menu:\n" \
"1. View profile\n" \
"2. Buy weapon\n" \
"3. Sell weapon\n" \
"4. Change status\n"
"5. Set weapon\n" \
"6. Unset weapon\n" \
"7. Exit";

char user_storage_prefix[] = "./users/\0";

user* g_user = NULL;

char weapon_list[48][32]= {
"Black March", "Blue August", "Boomerang Blade", "Cherry River Needle",
"Colorless December", "Cullinan", "Dark September", "Donghae", "El Robina", "Enryu's Thorn",
"Essence of Bravery", "Flying Fish Spear", "Golden November", "Great Blue Spear", 
"Green April", "Hook", "Indigo July", "Jeok's Wand", "Kranos", "Krishna",
"Lecalicus", "Living Ignition Weapon", "Luminous June", "Mad Shocker", "Mago",
"Mysterious Weapon", "Narumada", "Needle", "Orange Snake", "Red October",
"Shining Fan", "Shinsu Bomb", "Silver January", "Silver Moray",
"Sniper Rifle", "Spinel", "Stone General's Spear", "Sword", "Sylpheed",
"Unnamed Ancient Spear", "Vagnil", "Wand", "Spear", "White February",
"White Heavenly Mirror", "White Oar", "Woon's Hammer", "Yellow May"
};
int weapon_list_size = 48;
