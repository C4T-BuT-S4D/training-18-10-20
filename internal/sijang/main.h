#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <pthread.h>
#include <time.h>

#include <malloc.h>

typedef unsigned int DWORD;
typedef unsigned short int WORD;
typedef unsigned char BYTE;

// build conditions
//#define MACOS 1
#define DEBUG 1
#define LINUX 1

// some const
#define DEFAULT_ALARM_TIME 120
#define USERNAME_SIZE 128
#define PASSWORD_SIZE 256
#define FILENAME_SIZE 512
#define DEFUALT_BUF_SIZE 1024
#define DEFAULT_COINS_COUNT 512
#define SOUL_DESC_SIZE 256
#define WORD_MAX 0xffff

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
#define NORMAL_EXIT 0

// options
#define LOGIN 1 
#define REGISTER 2
#define EXIT 3

enum USER_MENU_OPTIONS { EMPTRY, VIEW_PROFILE, BUY_WEAPON, 
	SELL_WEAPON, SET_WEAPON, UNSET_WEAPON, USER_EXIT 
};

typedef struct {
	DWORD quality;
	char* name;
	char* description;
	BYTE is_seted;
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

// a->fd -> b->fd -> c 
// a->fd -> c -> null
// a->fd ->

typedef struct {
	weapon* wp;
	int m_cost;
	int u_cost;
	char* owner;
} add_to_market_args;

typedef struct {
	BYTE owner[ 32 ];
	DWORD cost;
	DWORD quality;
	BYTE desc[ 64 ];
	size_t timestamp;
} market_entry;

typedef struct {
	BYTE lock;
	DWORD size;
	market_entry** items;
} market;

// utils
void setup( void );
int read_int( void );
int read_buf( char*, int );
void* alloc_mem( size_t );
void free_mem( void* );
void sanitize( char* );
char** get_file_lines( char* );
char* get_user_filename( char* );
void print_menu( void );
int find_userfile( char* );
int read_coins( char* );

BYTE rand8( void );
WORD rand16( void );
DWORD rand32( void );

// user utils
void read_password( char*, char* );
int check_password( char*, char* );
int init_user( char* );
void reg_user( char*, char* );
int login( void );
int user_session( void );
int reg( void );
weapon* get_random_weapon( void );
BYTE* weapon2str( weapon* wp );
void parse_weapon_line( weapon* , char* );
void add_to_market_thr( weapon*, int, int );
void* add_to_market_hndl( void* args );

// user menu funcs
void view_profile( void );
void set_weapon( void );
void unset_weapon( void );
void sell_weapon( void );

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
"4. Set weapon\n" \
"5. Unset weapon\n" \
"6. Exit";

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
