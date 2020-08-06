#include "main.h"

int main( int argc, char* argv[], char* envp[] )
{
	setup();
	BYTE attempt = 3;

	while ( attempt )
	{
		print_menu();
		int option = read_int();

		if ( option > 3 || option < 0 )
		{
			puts( "[-] Incorrect option!" );
			return INCORRECT_OPTION;
		}

		switch( option )
		{
			case LOGIN:
			{
				if ( login() )
				{
					user_session();
				}
				break;
			}
			
			case REGISTER:
			{	
				if ( reg() )
				{
					user_session();
				}
				break;
			}

			case EXIT:
				return NORMAL_EXIT;
				break;

			default:
				return INCORRECT_OPTION;
		}

		attempt--;
	}

	return NORMAL_EXIT;
};

void setup( void )
{
	alarm( DEFAULT_ALARM_TIME );

	setvbuf( stdin,  0, 2, 0 );
	setvbuf( stdout, 0, 2, 0 );
	setvbuf( stderr, 0, 2, 0 );
};

void print_menu( void )
{
	puts( banner );
	puts( "" );

	puts( menu );
	printf( "> " );

};

void print_user_menu( void )
{
	puts( user_menu );
	printf( "> " );
};

int login( void )
{
	// check username
	printf( "[?] Enter username: " );
	char* username = (char*) alloc_mem( USERNAME_SIZE );

	read_buf( username, USERNAME_SIZE );
	sanitize( username );

	if ( strlen( username ) == 0 )
	{
		puts( "[-] Invalid username!" );
		return FALSE;
	}

	if ( !find_userfile( username ) )
	{
		puts( "[-] No such user!" );
		return FALSE;
	}

	// check password
	printf( "[?] Enter password: " );
	char* password = (char*) alloc_mem( PASSWORD_SIZE );

	read_buf( password, PASSWORD_SIZE );
	sanitize( password );

	if( strlen( password ) == 0 )
	{
		puts( "[-] Invalid password!" );
		return FALSE;
	}

	if( !check_password( username, password ) )
	{
		puts( "[-] Incorrect password!" );
		return FALSE;
	}

	init_user( username );
	free_mem( password );

	return TRUE;
};

int find_userfile( char* username )
{	
	char* full_filename = get_user_filename( username );

	#ifdef DEBUG
		printf( "[!] Filename: %s\n", full_filename );
	#endif

	if ( access( full_filename, F_OK ) != -1 )
	{
		return TRUE;
	}
	
	return FALSE;
};

int check_password( char* username, char* password )
{
	char* buf = (char*) alloc_mem( DEFUALT_BUF_SIZE );
	read_password( username, buf );

	#ifdef DEBUG
		printf( "[!] Read bufer from file: %s\n", buf );
	#endif

	if ( strlen( buf ) == 0 )
	{
		free( buf );
		return TRUE;
	}

	if ( !strncmp( buf, password, strlen( buf ) ) )
	{	
		free( buf );
		return TRUE;
	}

	free( buf );
	return FALSE;
};

int user_session( void )
{
	BYTE attempt = 0x7f;

	while ( attempt )
	{
		print_user_menu();
		int option = read_int();

		switch( option )
		{
			case VIEW_PROFILE:
				view_profile();
				break;
			case BUY_WEAPON:
				//buy_souls();
				break;
			case SELL_WEAPON:
				sell_weapon();
				break;
			case SET_WEAPON:
				set_weapon();
				break;
			case UNSET_WEAPON:
				unset_weapon();
				break;
			case USER_EXIT:
				return NORMAL_EXIT;
				break;
			default:
				attempt--;
				break;
		}
	}

	return NORMAL_EXIT;
};

int reg( void )
{
	printf( "[?] Enter username: " );
	char* username = (char*) alloc_mem( USERNAME_SIZE );

	read_buf( username, USERNAME_SIZE );
	sanitize( username );

	if ( strlen( username ) == 0 )
	{
		puts( "[-] Invalid username!" );
		return FALSE;
	}

	if ( find_userfile( username ) )
	{
		puts( "[-] User alredy exist!" );
		return FALSE;
	}

	printf( "[?] Enter password: " );
	char* password = (char*) alloc_mem( PASSWORD_SIZE );

	read_buf( password, PASSWORD_SIZE );
	sanitize( password );

	if( strlen( password ) == 0 )
	{
		puts( "[-] Invalid password!" );
		return FALSE;
	}

	reg_user( username, password );
	init_user( username );
	
	free_mem( password );
	return TRUE;
};

void reg_user( char* username, char* password )
{
	char* filename = get_user_filename( username );
	FILE* fp = fopen( filename, "w" );

	if ( fp == NULL )
	{
		perror( "[-] File open error!" );
		exit( FILE_OPEN_TO_WRITE_ERROR );
	}

	fprintf( fp, "%s\n", password );
	fprintf( fp, "%d\n", DEFAULT_COINS_COUNT );
	fprintf( fp, "%d\n", FALSE );

	weapon* start_weapon = get_random_weapon();
	BYTE* weapon_string = weapon2str( start_weapon );

	fprintf( fp, "%s\n", weapon_string );
	fclose( fp );
	free_mem( filename );
};

int init_user( char* username )
{
	if ( g_user != NULL )
	{
		puts( "[-] User already logined!" );
		return FALSE;
	}

	g_user = (user*) alloc_mem( sizeof( user ) );

	g_user->name = username;
	g_user->password = (char*) alloc_mem( PASSWORD_SIZE );

	read_password( username, g_user->password );
	g_user->coins = read_coins( username );

	#ifdef DEBUG
		printf( "g_user->name: %s\n", g_user->name );
		printf( "g_user->password: %s\n", g_user->password );
		printf( "g_user->coins: %d\n", g_user->coins );
	#endif

	char* filename = get_user_filename( username );
	char** file_data = get_file_lines( filename );
	
	if ( file_data[ 2 ][ 0 ] == '1' )
	{
		g_user->is_weapon_set = 1;
	}
	else
	{
		g_user->is_weapon_set = 0;
	}

	g_user->weapons = (weapon**) alloc_mem( sizeof( weapon* ) );
	g_user->weapon_count = 0;

	for ( int i = 3; file_data[ i ] != NULL; i++ )
	{
		weapon* wp = (weapon*) alloc_mem( sizeof( weapon ) );
		wp->is_seted = FALSE;
		parse_weapon_line( wp, file_data[ i ] );
		
		g_user->weapons[ g_user->weapon_count ] = wp;
		g_user->weapon_count++;

		g_user->weapons = (weapon**) realloc( g_user->weapons,
			sizeof( weapon* ) * ( g_user->weapon_count + 1 ) );
		
		g_user->weapons[ g_user->weapon_count ] = NULL;
	}

	for ( int i = 0; file_data[ i ] != NULL; i++ )
	{
		free_mem( file_data[ i ] );
	}
	
	free_mem( filename );
	return TRUE;
};

void view_profile( void )
{	
	puts( "========================================" );

	printf( "[ ---- %s ---- ]\n", g_user->name );
	printf( "[ Coins: %d ]\n", g_user->coins );
	printf( "[ Current weapon: " );

	if ( g_user->is_weapon_set )
		puts( g_user->current_weapon->name ); 
	else
		puts( "not set" );

	printf( "[ Weapons amount: %d ]\n", g_user->weapon_count );

	for ( int i = 0; i < g_user->weapon_count; i++ )
	{
		weapon* wp = g_user->weapons[ i ];

		printf( "[ Weapon: %s, quality: %d, desc: %s ]\n", 
			wp->name, wp->quality, wp->description );
	}

	puts( "========================================" );
};

void sell_weapon( void )
{
	if ( g_user->weapon_count > 0 )
	{
		puts( "[+] Your weapon: " );

		for ( int i = 0; g_user->weapons[ i ] != NULL; i++ )
		{
			printf( "[%d] %s\n", i, g_user->weapons[ i ]->name );
		}

		printf( "[?] Enter weapon id: " );
		int weapon_id = read_int();

		if ( weapon_id > g_user->weapon_count || weapon_id < 0 )
		{
			puts( "[-] Error id!" );
		}
		else
		{
			weapon* wp = g_user->weapons[ weapon_id ];

			printf( "[+] Quality of weapon: %d\n", wp->quality );
			int user_cost = (int)((float)wp->quality * 0.1);
			printf( "[+] You will receive [%d] coins\n", user_cost );
			int market_cost = wp->quality * 10;

			printf( "[?] Are you sure you want to sell this item?[y\\n]: " );
			
			char choice[ 4 ];
			read_buf( choice, 3 );

			if ( choice[ 0 ] == 'y' )
			{
				printf( "[?] Do you want set description?[y\\n]: " );
				read_buf( choice, 3 );

				if ( choice[ 0 ] == 'y' )
				{
					char* desc = (char*) alloc_mem( DEFUALT_BUF_SIZE );
					printf( "[?] Enter description: " );

					read_buf( desc, DEFUALT_BUF_SIZE );
					wp->description = desc;
				}

				add_to_market_thr( wp, market_cost, user_cost );
			}
		}
	}
	else
	{
		puts( "[-] You don't have any weapon!" );
	}
};

void set_weapon( void )
{
	if ( g_user->weapon_count > 0 )
	{
		puts( "[+] Your weapon: " );

		for ( int i = 0; g_user->weapons[ i ] != NULL; i++ )
		{
			printf( "[%d] %s\n", i, g_user->weapons[ i ]->name );
		}

		printf( "[?] Enter weapon id: " );
		int weapon_id = read_int();

		if ( weapon_id > g_user->weapon_count || weapon_id < 0 )
		{
			puts( "[-] Error id!" );
		}
		else
		{
			g_user->current_weapon = g_user->weapons[ weapon_id ];
			g_user->weapons[ weapon_id ]->is_seted = TRUE;
			g_user->is_weapon_set = TRUE;

			remove_weapon( weapon_id );

			printf( "[+] You set %s as your main weapon!\n", 
				g_user->current_weapon->name );
		}
	}
	else
	{
		puts( "[-] You don't have any weapon!" );
	}
}

void unset_weapon( void )
{
	if ( g_user->is_weapon_set )
	{
		add_weapon( g_user->current_weapon );

		g_user->current_weapon->is_seted = FALSE;
		g_user->current_weapon = NULL;
		g_user->is_weapon_set = FALSE;

		puts( "[+] Weapon removed!" );
	}
	else
	{
		puts( "[-] No main weapon!" );
	}
};

void add_to_market_thr( weapon* wp, int m_cost, int u_cost )
{
	pthread_t tid;
	pthread_attr_t attr;

	pthread_attr_init( &attr );

	add_to_market_args* args = (add_to_market_args*) alloc_mem( 
		sizeof( add_to_market_args  ) 
	);

	args->wp = wp;
	args->m_cost = m_cost;
	args->u_cost = u_cost;
	args->owner = g_user->name;

	pthread_create( &tid, &attr, add_to_market_hndl, (void*)args );

	//pthread_join( tid, NULL );
	puts( "[+] Item is added to market!" ); 
};

void* add_to_market_hndl( void* args )
{
	// todo
	// add_to_market_args* l_args = (add_to_market_args*) args;
	// sleep( 3 );
	// //puts( "exit from thread!" );
	// pthread_exit( 0 );
};

void remove_weapon( int id )
{
	if ( g_user->weapons[ id ] != NULL )
	{
		for ( int i = id; g_user->weapons[ i ] != NULL; i++ )
		{
			g_user->weapons[ i ] = g_user->weapons[ i + 1 ];
		}

		g_user->weapon_count--;	
	}
	else
	{
		printf( "[-] Weapon with id %d is not exist!\n", id );
	}
};

void add_weapon( weapon* wp )
{
	g_user->weapons[ g_user->weapon_count ] = wp;
	g_user->weapon_count++;

	g_user->weapons = (weapon**) realloc( g_user->weapons, 
		sizeof( weapon* ) * ( g_user->weapon_count + 1 ) );
	g_user->weapons[ g_user->weapon_count ] = NULL;
};

BYTE* weapon2str( weapon* wp )
{
	int size = 5; // max size of WORD - 65535 - 5 symbols
	BYTE is_desc = FALSE;

	if ( wp->name != NULL )
	{
		size += strlen( wp->name );
	}
	else
	{
		puts( "[-] Invalid struct!" );
		exit( INVALID_WEAPON_STRUCT );
	}

	if ( wp->description != NULL )
	{
		size += strlen( wp->description );
		is_desc = TRUE;
	}

	size += 2; // quality|name|desc

	BYTE* string = (BYTE*) alloc_mem( size + 16 );
	
	if ( is_desc )
		sprintf( (char*)string, "%d|%s|%s", wp->quality, wp->name, wp->description  );
	else
		sprintf( (char*)string, "%d|%s|%s", wp->quality, wp->name, "None" );

	return string;
};

void parse_weapon_line( weapon* wp, char* line )
{	
	char* part = strtok( line, "|" );

	if ( part == NULL )
	{
		puts( "[-] Invalid weapon string!" );
		exit( INVALID_WEAPON_STRING );
	}

	// set quality
	char* tmp_str = (char*) alloc_mem( strlen( part ) );
	strcpy( tmp_str, part );
	wp->quality = atoi( tmp_str );
	free_mem( tmp_str );

	// set name
	part = strtok( NULL, "|" );

	if ( part == NULL )
	{
		puts( "[-] Invalid weapon string!" );
		exit( INVALID_WEAPON_STRING );
	}

	tmp_str = (char*) alloc_mem( strlen( part ) );
	strcpy( tmp_str, part );
	wp->name = tmp_str;

	// set desc
	part = strtok( NULL, "|" );

	if ( part == NULL )
	{
		wp->description = "None";
	}
	else
	{
		char* desc_str = (char*) alloc_mem( strlen( part ) );
		strcpy( desc_str, part );
		wp->description = desc_str;
	}
};

weapon* get_random_weapon( void )
{
	weapon* wp = (weapon*) alloc_mem( sizeof( weapon ) );

	wp->quality = rand16();
	wp->name = weapon_list[ rand8() % weapon_list_size ];
	wp->description = NULL;

	return wp;
};

char** get_file_lines( char* filename )
{
	FILE* fp = fopen( filename, "r" );

	if ( fp == NULL )
	{
		perror( "[-] File open error!" );
		exit( FILE_OPEN_TO_READ_ERROR );
	}

	char** lines = (char**) alloc_mem( sizeof( char* ) );
	size_t lines_idx = 0;

	char* line = NULL;
	size_t line_size = 0;
	ssize_t nbytes;

	while ( ( nbytes = getline( &line, &line_size, fp ) ) != -1 )
	{
		if ( nbytes > 0 && line_size > 0 )
		{
			// #ifdef DEBUG
			// 	printf( "nbytes = %d, line_size = %d, line = %s\n", 
			// 		nbytes, line_size, line );
			// #endif
			
			char* line_copy = (char*) alloc_mem( nbytes );
			strncpy( line_copy, line, nbytes );

			if ( line_copy[ nbytes - 1 ] == '\n' )
			{
				line_copy[ nbytes - 1 ] = '\0';
			}

			if ( strlen( line_copy ) != 0 )
			{
				lines[ lines_idx ] = line_copy;

				// #ifdef DEBUG
				// 	printf( "line =%p\n", line_copy );
				// 	printf( "lines[%d] = %p\n", lines_idx, lines[ lines_idx ] );
				// #endif
				
				lines_idx++;
				lines = (char**) realloc( lines, sizeof( char* ) * 
					( lines_idx + 1 ) ); 
				lines[ lines_idx ] = NULL;
			}
		}
	}

	fclose( fp );
	free_mem( filename );
	return lines;
};

int read_coins( char* username )
{
	char* filename = get_user_filename( username );

	FILE* fp = fopen( filename, "r" );

	if ( fp == NULL )
	{
		perror( "[-] File open error!" );
		exit( FILE_OPEN_TO_READ_ERROR );
	}

	size_t tmp = 0;

	fseek( fp, strlen( g_user->password )+1, SEEK_SET );
	fscanf( fp, "%d", &tmp );
	fclose( fp );

	free_mem( filename );

	return tmp;
};

void read_password( char* username, char* buf )
{
	char* filename = get_user_filename( username );

	FILE* fp = fopen( filename, "r" );

	if ( fp == NULL )
	{
		perror( "[-] File open error!" );
		exit( FILE_OPEN_TO_READ_ERROR );
	}

	fscanf( fp, "%s", buf );
	fclose( fp );
	free_mem( filename );
};

char* get_user_filename( char* username )
{
	char* full_filename = (char*) alloc_mem( FILENAME_SIZE );

	strncpy( full_filename, 
		user_storage_prefix, 
		strlen( user_storage_prefix ) 
	);

	strcat( full_filename, username );

	return full_filename;
};

int read_int( void )
{
	char buf[ 8 ];
	int nbytes = read( 0, buf, 8 );

	if ( nbytes > 0 )
	{
		if ( buf[ nbytes - 1 ] == '\n' )
			buf[ nbytes - 1 ] = '\0';
	}

	int result = 0;
	result = atoi( buf );

	return result;
};

int read_buf( char* buf, int max_size )
{
	int nbytes = 0;

	nbytes = read( 0, buf, max_size );

	if ( nbytes > 0 )
	{
		if ( buf[ nbytes - 1 ] == '\n' )
		{
			buf[ nbytes - 1 ] = 0;
		}
	}

	return nbytes;
};

void* alloc_mem( size_t size )
{
	void* ptr = calloc( size, 1 );

	if ( ptr == NULL )
	{
		perror( "[-] Allocation error!" );
		exit( MALLOC_ERROR );
	}

	return ptr;
};

void free_mem( void* ptr )
{
	if ( ptr != NULL )
	{	
		size_t chunk_size = 0;

		#ifdef MACOS
			chunk_size = malloc_size( ptr );
		#endif

		#ifdef LINUX
			chunk_size = malloc_usable_size( ptr );
		#endif

		if ( chunk_size == 0 )
		{
			perror( "[-] Corrupted chunk discovered!" );
			exit( FREE_CHUNK_ERROR );
		}

		memset( ptr, 0, chunk_size );
		free( ptr );
	}
};

void sanitize( char* buf )
{
	size_t buf_size = strlen( buf );

	for ( int i = 0; i < buf_size; i++ )
	{
		if ( ( buf[ i ] >= 'a' && buf[ i ] <= 'z' ) || 
			 ( buf[ i ] >= 'A' && buf[ i ] <= 'Z' ) ||
			 ( buf[ i ] >= '0' && buf[ i ] <= '9') )
		{
			;
		}
		else
		{
			buf[ i ] = '\0';
		}
	}
};

BYTE rand8( void )
{
	FILE* fp = fopen( "/dev/urandom", "r" );
	
	if ( fp == NULL )
	{
		perror( "[-] File open error!" );
		exit( FILE_OPEN_TO_READ_ERROR );
	}

	BYTE* tmp_buf = (BYTE*) alloc_mem( DEFUALT_BUF_SIZE * sizeof( BYTE ) );
	fread( tmp_buf, sizeof( BYTE ), DEFUALT_BUF_SIZE, fp );
	fclose( fp );

	BYTE value = tmp_buf[ rand() % DEFUALT_BUF_SIZE ];
	free_mem( tmp_buf );

	return value;
};

WORD rand16( void )
{
	FILE* fp = fopen( "/dev/urandom", "r" );
	
	if ( fp == NULL )
	{
		perror( "[-] File open error!" );
		exit( FILE_OPEN_TO_READ_ERROR );
	}

	WORD* tmp_buf = (WORD*) alloc_mem( DEFUALT_BUF_SIZE * sizeof( WORD ) );
	fread( tmp_buf, sizeof( WORD ), DEFUALT_BUF_SIZE, fp );
	fclose( fp );

	WORD value = tmp_buf[ rand() % DEFUALT_BUF_SIZE ];
	free_mem( tmp_buf );
	
	return value;
};

DWORD rand32( void )
{
	FILE* fp = fopen( "/dev/urandom", "r" );
	
	if ( fp == NULL )
	{
		perror( "[-] File open error!" );
		exit( FILE_OPEN_TO_READ_ERROR );
	}

	DWORD* tmp_buf = (DWORD*) alloc_mem( DEFUALT_BUF_SIZE * sizeof( DWORD ) );
	fread( tmp_buf, sizeof( DWORD ), DEFUALT_BUF_SIZE, fp );
	fclose( fp );

	DWORD value = tmp_buf[ rand() % DEFUALT_BUF_SIZE ];
	free_mem( tmp_buf );
	
	return value;
};