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

	if ( access( full_filename, F_OK ) != -1 )
	{
		free_mem( full_filename );
		return TRUE;
	}

	free_mem( full_filename );
	return FALSE;
};

int check_password( char* username, char* password )
{
	char* buf = (char*) alloc_mem( DEFUALT_BUF_SIZE );
	read_password( username, buf );

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
				buy_weapon();
				break;
			case SELL_WEAPON:
				sell_weapon();
				break;
			case CHANGE_STATUS:
				change_weapon_status();
				break;
			case SET_WEAPON:
				set_weapon();
				break;
			case UNSET_WEAPON:
				unset_weapon();
				break;
			case USER_EXIT:
			{
				save_current_user();

				free_mem( g_user->name );
				g_user->name = NULL;
				free_mem( g_user->password );
				g_user->password = NULL;

				if ( g_user->is_weapon_set )
					free_weapon( g_user->current_weapon );

				g_user->current_weapon = NULL;

				for ( int i = 0; i < g_user->weapon_count; i++ )
				{
					if ( g_user->weapons[ i ] != NULL )
					{
						free_weapon( g_user->weapons[ i ] );
						g_user->weapons[ i ] = NULL;
					}
					else
						break;
				}
				
				free_mem( g_user->weapons );
				g_user->weapons = NULL;

				free_mem( g_user );
				g_user = NULL;
				
				return NORMAL_EXIT;
			}
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

	char* filename = get_user_filename( username );
	char** file_data = get_file_lines( filename );
	filename = NULL;
	
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
		file_data[ i ] = NULL;
	}

	return TRUE;
};

int save_current_user( void )
{
	char* filename = get_user_filename( g_user->name );
	FILE* fp = fopen( filename, "w" );

	if ( fp == NULL )
	{
		perror( "[-] File open error!" );
		exit( FILE_OPEN_TO_WRITE_ERROR );
	}

	fprintf( fp, "%s\n", g_user->password );
	fprintf( fp, "%d\n", g_user->coins );

	if ( g_user->is_weapon_set )
	{
		unset_weapon();
	}

	fprintf( fp, "%d\n", FALSE );

	if ( g_user->weapon_count != 0 )
	{
		for ( int i = 0; i < g_user->weapon_count; i++ )
		{
			if ( g_user->weapons[ i ] != NULL )
			{
				BYTE* wp_string = weapon2str( g_user->weapons[ i ] );
				if ( wp_string != NULL )
					fprintf( fp, "%s\n", wp_string );
			}
		}
	}

	fclose( fp );
	free_mem( filename );

	return 0;
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

int buy_weapon( void )
{
	// try to get items from server
	int current_page = 0;
	page_item** page = (page_item**) alloc_mem( sizeof( page_item* ) * 10 );

	enum MARKET_CODES ret_code = get_items_from_server( current_page, page );

	if ( ret_code == MARKET_IS_EMPTY )
		return 1;

	// print header if not empty
	printf( table_header );
	
	for ( int i = 0; i < 10 && page[ i ]; i++ )
	{
		printf( "+  %d  |--|%28s|--|  %6lld  |--|%13u|\n", i, 
			page[ i ]->name, page[ i ]->cost, page[ i ]->token
		);
		puts( "+-----+--+----------------------------+--+----------+--+-------------+" );
	}

	int max_menu_inputs = 50;

	while ( TRUE && max_menu_inputs > 0 )
	{
		puts( " -- Buy Menu -- " );
		puts( "1. Buy item by token" );
		puts( "2. Buy item by page id" );
		puts( "3. Get another page" );
		puts( "4. Exit" );
		printf( "> " );
		
		int option = read_int();
		
		switch( option )
		{
			case 1:
				buy_by_token( page );
				break;
			case 2:
				buy_by_page_id( page );
				break;
			case 3:
				get_another_page( page );
				break;
			case 4:
				return 0;
				break;
			default:
				break;
		}

		max_menu_inputs -= 1;
	}

	for ( int i = 0; i < 10; i++ )
	{	
		if ( page[ i ] == NULL )
			continue;

		free_mem( page[ i ]->name );
		free_mem( page[ i ] );
		page[ i ] = NULL;
	}

	return 0;
};

enum MARKET_CODES get_items_from_server( int page_id, page_item** page )
{
	int market_fd = connect_to_market();

	if ( market_fd == -1 )
	{
		puts( "[-] Item is not added to market!" );
		pthread_exit( 0 );
	}

	// try to get access to market
	char* packet = (char*) alloc_mem( REQ_TO_ADD_PACKET_SIZE );
	sprintf( packet, "%s|get_page", g_user->name );
	int size = (int) strlen( packet );

	enum MARKET_CODES ret_code = request_to_access( packet, size, market_fd );
	int tries = 0;

	while ( ret_code == MARKET_BUSY )
	{
		ret_code = request_to_access( packet, size, market_fd );
		usleep( SLEEP_TIME );

		if ( ret_code != MARKET_BUSY )
			break;

		if ( tries > SLEEP_TRIES )
			break;

		tries += 1;
	}

	if ( ret_code == MARKET_BUSY )
	{
		printf( "[-] Market is busy now! Try to another time!" );
		return ret_code;
	}

	// get pages 
	free_mem( packet );
	packet = (char*) alloc_mem( MARKET_ITEM_SIZE );

	sprintf( packet, "get_page|%d|%d|", page_id, PAGE_SIZE );

	ret_code = send_req( market_fd, packet );

	if ( ret_code == MARKET_IS_EMPTY )
	{
		puts( "[-] Market is empty!" );
		return ret_code;
	}

	if ( ret_code == MARKET_PAGE_ITEMS_GETED )
	{
		// get data from server
		char* server_data = alloc_mem( MARKET_ITEM_SIZE * PAGE_SIZE );
		recv( market_fd, server_data, MARKET_ITEM_SIZE * PAGE_SIZE, 0 );
		
		// proceed page data
		char* ptr = strtok( server_data, "\n" );
		char** lines = (char**) alloc_mem( sizeof( char* ) * PAGE_SIZE );

		for ( int i = 0; ptr; i++ )
		{
			lines[ i ] = (char*) alloc_mem( strlen( ptr ) );
			strcpy( lines[ i ], ptr + 5 );
			ptr = strtok( NULL, "\n" );
		}

		for ( int i = 0; lines[ i ]; i++ )
		{
			page[ i ] = (page_item*) alloc_mem( sizeof( page_item ) );

			char* ptr = strtok( lines[ i ], "|" );
			page[ i ]->name = (char*) alloc_mem( strlen( ptr ) );
			strcpy( page[ i ]->name, ptr );

			ptr = strtok( NULL, "|" );
			page[ i ]->cost = atoi( ptr );

			ptr = strtok( NULL, "|" );
			page[ i ]->token = atoi( ptr );

			page[ i ]->id = i;
		}

		for ( int i = 0; lines[ i ]; i++ )
		{
			free_mem( lines[ i ] );
		}

		free_mem( lines );
		free_mem( server_data );
	}

	close_connection( market_fd );
	return ret_code;
};

int buy_by_token( page_item** page )
{
	printf( "[?] Enter item token: " );
	DWORD token = read_int();

	market_item* item = (market_item*) alloc_mem( sizeof( market_item ) );

	// active wait to get data
	int tries = 0;
	enum MARKET_CODES status = request_item_info( token, item );

	if ( status == MARKET_BUSY )
	{
		printf( "[!] Waiting response of market!" );
	}

	while ( item == NULL && status == MARKET_BUSY )
	{
		printf( "." );

		status = request_item_info( token, item );
		
		if ( status != MARKET_BUSY )
			break;

		if ( tries > SLEEP_TRIES )
			break;

		usleep( SLEEP_TIME );
		tries += 1;
	}

	if ( status == MARKET_ITEM_NOT_FOUND )
	{
		printf( "[-] Item with token <%u> not found!\n", token );
		return MARKET_ITEM_NOT_FOUND;
	}

	if ( status == MARKET_BUSY )
	{
		puts( "[-] Market is busy now, try to another time!" );
		return MARKET_BUSY;
	}

	if ( item->cost > g_user->coins )
	{
		puts( "[-] You dont have money to buy this item!" );
		return NOT_ENOUGH_MONEY;
	}

	printf( "[+] You really want to buy this weapon?[y\\n]: " );
	char choice[ 4 ];
	read_buf( choice, 3 );

	if ( choice[ 0 ] == 'y' )
	{	
		status = buy( token, item );
	}

	if ( status == MARKET_ITEM_DELETED )
	{
		for ( int i = 0; i < 10; i++ )
		{
			if ( page[ i ] == NULL )
				continue;

			if ( page[ i ]->token == token )
			{
				free_mem( page[ i ]->name );
				free_mem( page[ i ] );
				page[ i ] = NULL;
			}
		}
	}

	return 0;
};


enum MARKET_CODES buy( DWORD token, market_item* item )
{
	// buy item
	int tries = 0;
	enum MARKET_CODES status = buy_item( token, item );

	if ( status == MARKET_BUSY )
	{
		printf( "[!] Waiting response of market!" );
	}

	while ( item == NULL && status == MARKET_BUSY )
	{
		printf( "." );

		status = buy_item( token, item );
		
		if ( status != MARKET_BUSY )
			break;

		if ( tries > SLEEP_TRIES )
			break;

		usleep( SLEEP_TIME );
		tries += 1;
	}

	if ( status == MARKET_BUSY )
	{
		printf( "[-] Market is busy now! Try another time!" );
		return MARKET_BUSY;
	}

	if ( status == MARKET_ITEM_DELETED && item != NULL )
	{
		if ( item->archive )
		{
			printf( "[!!] You cant buy archived item <%s> with description <%s>!\n",
				item->name, item->desc 
			);
			
			free_mem( item->name );
			free_mem( item->owner );
			free_mem( item->desc );
			free_mem( item );
			
			return status;
		}

		g_user->coins -= item->cost;
		//convert_market_item()
		puts( "[+] You have successfully purchased an item!" );
		puts( " --- Item --- " );
		printf( "Name: %s\n", item->name );
		printf( "Description: %s\n", item->desc );
		printf( "Cost: %d\n", item->cost );
		printf( "Quality: %d\n", item->quality );
		printf( "Owner: %s\n", item->owner );
		printf( "Archived: %d\n", item->archive );
		printf( "Token: %u\n", item->token );

		// make weapon
		weapon* new_weapon = (weapon*) alloc_mem( sizeof( weapon ) );
		// add name
		new_weapon->name = (char*) alloc_mem( strlen( item->name ) );
		strcpy( new_weapon->name, item->name );

		// add description
		new_weapon->description = (char*) alloc_mem( strlen( item->desc ) );
		strcpy( new_weapon->description, item->desc );

		// add quality
		new_weapon->quality = item->quality;
		new_weapon->is_seted = FALSE;

		add_weapon( new_weapon );
		save_current_user();

		// free item
		free_mem( item->name );
		free_mem( item->owner );
		free_mem( item->desc );
		free_mem( item );
	}

	return status;
};

enum MARKET_CODES buy_item( DWORD token, market_item* itm )
{
	int market_fd = connect_to_market();

	if ( market_fd == -1 )
	{
		puts( "[-] Item is not added to market!" );
		pthread_exit( 0 );
	}

	// try to get access to market
	char* packet = (char*) alloc_mem( REQ_TO_ADD_PACKET_SIZE );
	sprintf( packet, "%s|del_item", g_user->name );
	int size = (int) strlen( packet );

	enum MARKET_CODES ret_code = request_to_access( packet, size, market_fd );
	free_mem( packet );

	if ( ret_code == MARKET_BUSY )
	{
		close_connection( market_fd );
		return ret_code;
	}

	// if we got access to market
	packet = (char*) alloc_mem( MARKET_ITEM_SIZE );

	// add comand
	sprintf( packet, "del_item|%u|", token );

	ret_code = send_req( market_fd, packet );

	if ( ret_code == MARKET_ITEM_DELETED || ret_code == MARKET_ITEM_FULLINFO )
	{
		char* ptr = strtok( packet, "|" );
		// copy name to struct
		ptr = strtok( NULL, "|" );
		itm->name = (char*) alloc_mem( strlen( ptr ) );
		strcpy( itm->name, ptr );

		// copy description to struct
		ptr = strtok( NULL, "|" );
		itm->desc = (char*) alloc_mem( strlen( ptr ) );
		strcpy( itm->desc, ptr );

		// copy cost to struct
		ptr = strtok( NULL, "|" );
		itm->cost = atoi( ptr );

		// copy quality to struct
		ptr = strtok( NULL, "|" );
		itm->quality = atoi( ptr );

		// copy owner to struct
		ptr = strtok( NULL, "|" );
		itm->owner = (char*) alloc_mem( strlen( ptr ) );
		strcpy( itm->owner, ptr );

		// set is archived
		ptr = strtok( NULL, "|" );

		if ( atoi( ptr ) == 1 )
			itm->archive = TRUE;
		else
			itm->archive = FALSE;

		// set token
		ptr = strtok( NULL, "|" );
		itm->token = atoi( ptr );
	}

	if ( ret_code == MARKET_ITEM_FULLINFO )
		ret_code = MARKET_ITEM_DELETED;

	return ret_code;
};

int buy_by_page_id( page_item** page )
{
	printf( "[?] Enter id: " );
	int id = read_int();

	if ( id < 0 || id > 9 || page[ id ] == NULL )
	{
		puts( "[-] Incorrect id!" );
		return id;
	}

	if ( page[ id ]->cost > g_user->coins )
	{
		puts( "[-] You dont have money to buy this item!" );
		return NOT_ENOUGH_MONEY;
	}

	market_item* itm = (market_item*) alloc_mem( sizeof( market_item ) );
	DWORD token = page[ id ]->token;

	free_mem( page[ id ]->name );
	free_mem( page[ id ] );
	page[ id ] = NULL;

	return buy( token, itm );
};

int get_another_page( page_item** page )
{
	printf( "[?] Enter page id: " );
	int page_id = read_int();

	// todo, add wrapper on sever handler
	return 0;
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
					char* desc = (char*) alloc_mem( DESCRIPTION_SIZE );
					printf( "[?] Enter description: " );

					read_buf( desc, DESCRIPTION_SIZE );
					sanitize( desc );
					wp->description = desc;
				}

				printf( "[+] Archive your weapon?[y\\n]: " );
				read_buf( choice, 3 );

				if ( choice[ 0 ] == 'y' )
					add_to_market_thr( wp, market_cost, user_cost, 1 );
				else
					add_to_market_thr( wp, market_cost, user_cost, 0 );
			}
		}
	}
	else
	{
		puts( "[-] You don't have any weapon!" );
	}
};

int change_weapon_status( void )
{
	printf( "[?] Enter weapon token: " );
	DWORD user_token = read_int();

	market_item *weapon = (market_item*) alloc_mem( sizeof( market_item ) );
	// active wait to get weapon data

	int tries = 0;
	int status = request_full_item_info( user_token, weapon );

	if ( status == MARKET_BUSY )
	{
		printf( "[!] Waiting response of market!" );
	}

	while ( weapon == NULL && status == MARKET_BUSY )
	{
		printf( "." );

		status = request_full_item_info( user_token, weapon );
		
		if ( status != MARKET_BUSY )
			break;

		if ( tries > SLEEP_TRIES )
			break;

		usleep( SLEEP_TIME );
		tries += 1;
	}

	if ( status == MARKET_ITEM_NOT_FOUND )
	{
		printf( "[-] Item with token <%u> not found!\n", user_token );
		return MARKET_ITEM_NOT_FOUND;
	}

	if ( status == MARKET_ITEM_ACCESS_ERR )
	{
		puts( "[-] You cant change info for this item!" );
		return MARKET_ITEM_ACCESS_ERR;
	}

	if ( status == MARKET_BUSY )
	{
		puts( "[-] Market is busy now, try to another time!" );
		return MARKET_BUSY;
	}

	// printf full item info
	puts( "-------- Item info --------" );
	printf( "Name: %s\n", weapon->name );
	printf( "Description: %s\n", weapon->desc );
	printf( "Cost: %d\n", weapon->cost );
	printf( "Quality: %d\n", weapon->quality );
	printf( "Owner: %s\n", weapon->owner );
	printf( "Token: %u\n", weapon->token );
	printf( "Archived: %d\n", weapon->archive );
	puts( "---------------------------" );

	printf( "[?] Do you want change archive status? [y\\n]: " );
	char choice[ 4 ];
	int nbytes = read_buf( choice, 3 );
	choice[ nbytes - 1 ] = '\0';

	if ( choice[ 0 ] == 'y' )
	{
		if ( weapon->archive )
			weapon->archive = 0;
		else
			weapon->archive = 1;

		status = update_item_request( weapon );
		int tries = 0;

		while ( status == MARKET_BUSY )
		{
			usleep( SLEEP_TIME );
			status = update_item_request( weapon );

			if ( tries > SLEEP_TRIES )
				break;

			tries += 1;
		}

		if ( status == MARKET_BUSY )
		{
			puts( "[-] Market is busy now. Cant update item info!" );
			puts( "[-] Try to update after some time!" );
			return MARKET_BUSY;
		}

		if ( status == MARKET_ITEM_NOT_FOUND )
		{
			puts( "[-] Item for update not found!" );
			return status;
		}

		if ( status == MARKET_ITEM_UPDATED )
		{
			puts( "[+] Item updated!" );
			return status;
		}
	} 

	return status;
};

enum MARKET_CODES update_item_request( market_item* itm )
{
	int market_fd = connect_to_market();

	if ( market_fd == -1 )
	{
		puts( "[-] Item is not added to market!" );
		pthread_exit( 0 );
	}

	// try to get access to market
	char* packet = (char*) alloc_mem( REQ_TO_ADD_PACKET_SIZE );
	sprintf( packet, "%s|update", g_user->name );
	int size = (int) strlen( packet );

	enum MARKET_CODES ret_code = request_to_access( packet, size, market_fd );
	free_mem( packet );

	if ( ret_code == MARKET_BUSY )
	{
		close_connection( market_fd );
		return ret_code;
	}

	// if we got access to market
	// max possible size = 188
	char* req_packet = (char*) alloc_mem( MARKET_ITEM_SIZE );

	// add comand
	sprintf( req_packet, "update|%s|%s|%d|%d|%s|%d|%u|%s|",
		itm->name, itm->desc, itm->cost, itm->quality, itm->owner,
		itm->archive, itm->token, g_user->password
	);

	ret_code = send_req( market_fd, req_packet );

	return ret_code;
};

enum MARKET_CODES request_item_info( DWORD token, market_item* wp )
{
	int market_fd = connect_to_market();

	if ( market_fd == -1 )
	{
		puts( "[-] Item is not added to market!" );
		pthread_exit( 0 );
	}

	// try to get access to market
	char* packet = (char*) alloc_mem( REQ_TO_ADD_PACKET_SIZE );
	sprintf( packet, "%s|item_info", g_user->name );
	int size = (int) strlen( packet );

	enum MARKET_CODES ret_code = request_to_access( packet, size, market_fd );
	free_mem( packet );

	if ( ret_code == MARKET_BUSY )
	{
		close_connection( market_fd );
		return ret_code;
	}

	// if we got access to market
	packet = (char*) alloc_mem( MARKET_ITEM_SIZE );

	// add comand
	sprintf( packet, "item_info|%u|", token );

	ret_code = send_req( market_fd, packet );

	if ( ret_code == MARKET_ITEM_INFO )
	{
		char* ptr = strtok( packet, "|" );
		// copy name to struct
		ptr = strtok( NULL, "|" );
		wp->name = (char*) alloc_mem( strlen( ptr ) );
		strcpy( wp->name, ptr );

		// copy cost to struct
		ptr = strtok( NULL, "|" );
		wp->cost = atoi( ptr );

		// copy quality to struct
		ptr = strtok( NULL, "|" );
		wp->quality = atoi( ptr );

		// copy owner to struct
		ptr = strtok( NULL, "|" );
		wp->owner = (char*) alloc_mem( strlen( ptr ) );
		strcpy( wp->owner, ptr );

		// set is archived
		ptr = strtok( NULL, "|" );

		if ( atoi( ptr ) == 1 )
			wp->archive = TRUE;
		else
			wp->archive = FALSE;

		// set token
		ptr = strtok( NULL, "|" );
		wp->token = atoi( ptr );
	}

	close_connection( market_fd );
	free_mem( packet );
	return ret_code;
};

enum MARKET_CODES request_full_item_info( DWORD token, market_item* wp )
{
	int market_fd = connect_to_market();

	if ( market_fd == -1 )
	{
		puts( "[-] Item is not added to market!" );
		pthread_exit( 0 );
	}

	// try to get access to market
	char* packet = (char*) alloc_mem( REQ_TO_ADD_PACKET_SIZE );
	sprintf( packet, "%s|full_item_info", g_user->name );
	int size = (int) strlen( packet );

	enum MARKET_CODES ret_code = request_to_access( packet, size, market_fd );
	free_mem( packet );

	if ( ret_code == MARKET_BUSY )
	{
		close_connection( market_fd );
		return ret_code;
	}

	// if we got access to market
	packet = (char*) alloc_mem( MARKET_ITEM_SIZE );

	// add comand
	sprintf( packet, "full_item_info|%u|%s|%s|", 
		token, g_user->name, g_user->password 
	);

	ret_code = send_req( market_fd, packet );

	if ( ret_code == MARKET_ITEM_FULLINFO )
	{
		char* ptr = strtok( packet, "|" );
		// copy name to struct
		ptr = strtok( NULL, "|" );
		wp->name = (char*) alloc_mem( strlen( ptr ) );
		strcpy( wp->name, ptr );

		// copy description to struct
		ptr = strtok( NULL, "|" );
		wp->desc = (char*) alloc_mem( strlen( ptr ) );
		strcpy( wp->desc, ptr );

		// copy cost to struct
		ptr = strtok( NULL, "|" );
		wp->cost = atoi( ptr );

		// copy quality to struct
		ptr = strtok( NULL, "|" );
		wp->quality = atoi( ptr );

		// copy owner to struct
		ptr = strtok( NULL, "|" );
		wp->owner = (char*) alloc_mem( strlen( ptr ) );
		strcpy( wp->owner, ptr );

		// set is archived
		ptr = strtok( NULL, "|" );

		if ( atoi( ptr ) == 1 )
			wp->archive = TRUE;
		else
			wp->archive = FALSE;

		// set token
		ptr = strtok( NULL, "|" );
		wp->token = atoi( ptr );
	}

	close_connection( market_fd );
	free_mem( packet );
	return ret_code;
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

			remove_weapon_by_id( weapon_id );

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

void add_to_market_thr( weapon* wp, int m_cost, int u_cost, BYTE is_archive )
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
	args->archive = is_archive;

	pthread_create( &tid, &attr, add_to_market_hndl, (void*)args );
};

void* add_to_market_hndl( void* args )
{
	add_to_market_args* l_args = (add_to_market_args*) args;

	// try to connect to server
	int market_fd = connect_to_market();

	if ( market_fd == -1 )
	{
		puts( "[-] Item is not added to market!" );
		pthread_exit( 0 );
	}

	// try to lock access to market
	int status = request_to_add_item( market_fd );
	int tries = 0;

	// wait if market is busy
	if ( status == MARKET_BUSY )
	{	// wait 2.5 sec
		while ( TRUE && tries != SLEEP_TRIES )
		{
			usleep( SLEEP_TIME ); // 1000000 microsec == 1 sec 
			status = request_to_add_item( market_fd );
			
			if ( status == MARKET_ACCESS )
				break;
			tries++;
		}
	}

	// check if we can get access
	if ( status != MARKET_ACCESS )
	{
		puts( "[-] Market is busy now, try to wait some time!" );
		pthread_exit( NULL );
	}

	// create market item struct and fill it
	char* desc = l_args->wp->description;
	char* name = l_args->wp->name;
	DWORD quality = l_args->wp->quality;

	market_item* new_item = (market_item*) alloc_mem( sizeof( market_item ) );	
	DWORD item_token = rand32();

	new_item->name = name;
	new_item->owner = g_user->name;
	new_item->desc = desc;
	new_item->cost = l_args->m_cost;
	new_item->quality = quality;
	new_item->archive = l_args->archive;
	new_item->token = item_token;

	// convert market_item to request string
	char* req_packet = market_item2request( new_item );

	if ( req_packet == NULL )
	{
		perror( "[-] Invalid request packet!" );
		exit( INVALID_REQUEST_PACKET );
	}

	// send add request
	status = send_req( market_fd, req_packet ); // custom send function

	// check request status
	if ( status == MARKET_ITEM_ADDED )
	{	
		// add coins and delete weapon from weapon list
		g_user->coins += l_args->u_cost;
		remove_weapon( name, quality );
		
		puts( "[+] Item is added to market!" );
		printf( "[+] You can view your item by token: %u\n", item_token );

		free_mem( l_args->wp );

		save_current_user();
	}
	else if ( status == MARKET_ITEM_NOT_ADDED )
	{
		puts( "[-] Item not added to market!" );
		close_connection( market_fd );
		pthread_exit( 0 );
	}
	else
	{
		printf( "[-] Error in market add item request, errno = %d\n", status );
		close_connection( market_fd );
		pthread_exit( 0 );
	}

	close_connection( market_fd );
	pthread_exit( 0 );
};

int request_to_add_item( int fd )
{
	char* req_packet = (char*) alloc_mem( REQ_TO_ADD_PACKET_SIZE );
	sprintf( req_packet, "%s|add_item", g_user->name );
	int packet_size = (int) strlen( req_packet );

	enum MARKET_CODES ret_code = request_to_access( req_packet, packet_size, fd );

	if ( ret_code == -1 )
	{
		perror( "[-] Intrenal error!" );
		exit( INTERNAL_ERROR );
	}

	return ret_code;
};

enum MARKET_CODES request_to_access( char* req_packet, int packet_size, int fd )
{
	int nbytes = send( fd, (void*) req_packet, packet_size, 0 );

	// try to resend part of packet
	if ( (nbytes != packet_size) && (nbytes > 0) )
	{
		int pad = send( fd, (void*)( req_packet + nbytes ), 
			packet_size - nbytes, 0 );
		
		if ( ( pad + nbytes ) != packet_size )
		{
			perror( "[-] Some error in market server communication!" );
			exit( MARKET_SEND_REQ_ERROR );		
		}
	}

	free_mem( req_packet );
	req_packet = (char*) alloc_mem( REQ_TO_ADD_PACKET_SIZE );

	struct timeval tv;
	tv.tv_sec = RECV_TIMEOUT;
	tv.tv_usec = 0;
	setsockopt( fd, SOL_SOCKET, SO_RCVTIMEO, (const char*)&tv, sizeof( tv ) );

	nbytes = recv( fd, req_packet, REQ_TO_ADD_PACKET_SIZE, 0 );

	if ( nbytes < 0 )
	{
		perror( "[-] Some error in receive market data!" );
		exit( MARKET_GET_RECV_ERROR );
	}

	if ( !strncmp( req_packet, "access", 6 ) )
	{
		return MARKET_ACCESS;
	}
	else if ( !strncmp( req_packet, "busy", 4 ) )
	{
		return MARKET_BUSY;
	}
	else
	{
		perror( "[-] Some internal market error!" );
		exit( MARKET_INTERNRAL_ERROR );
	}

	return -1;
};

char* market_item2request( market_item* itm )
{
	if ( itm == NULL )
	{
		perror( "[-] Iterm pointer is NULL!" );
		exit( INVALID_ITEM_POINTER );
	}

	// max possible size = 188
	char* req_packet = (char*) alloc_mem( MARKET_ITEM_SIZE );

	// add comand
	sprintf( req_packet, "add_to_market|%s|%s|%d|%d|%s|%d|%u|%s|",
		itm->name, itm->desc, itm->cost, itm->quality, itm->owner,
		itm->archive, itm->token, g_user->password 
	);

	return req_packet;
};

int send_req( int fd, char* packet )
{
	int nbytes = send( fd, packet, MARKET_ITEM_SIZE, 0 );

	if ( nbytes != MARKET_ITEM_SIZE && nbytes > 0 )
	{
		int p_s = send( fd, packet + nbytes, MARKET_ITEM_SIZE - nbytes, 0 );

		if ( p_s + nbytes != MARKET_ITEM_SIZE )
		{
			perror( "[-] Some error in data send to market!" );
			return MARKET_ITEM_NOT_ADDED;
		}
	}

	char* recv_packet = (char*) alloc_mem( DEFUALT_BUF_SIZE );
	recv( fd, recv_packet, DEFUALT_BUF_SIZE, 0 );

	if ( !strncmp( recv_packet, "item_added\0", 10 ) )
	{
		free_mem( recv_packet );
		return MARKET_ITEM_ADDED;
	}
	else if ( !strncmp( recv_packet, "item_not_added\0", 14 ) )
	{
		free_mem( recv_packet );
		return MARKET_ITEM_NOT_ADDED;
	}
	else if ( !strncmp( recv_packet, "item_not_found\0", 14 ) )
	{
		free_mem( recv_packet );
		return MARKET_ITEM_NOT_FOUND;
	}
	else if ( !strncmp( recv_packet, "access_denied\0", 13 ) )
	{
		free_mem( recv_packet );
		return MARKET_ITEM_ACCESS_ERR;
	}
	else if ( !strncmp( recv_packet, "full_item_info|\0", 15 ) )
	{
		memcpy( packet, recv_packet, MARKET_ITEM_SIZE );
		return MARKET_ITEM_FULLINFO;
	}
	else if ( !strncmp( recv_packet, "item_updated|\0", 12 ) )
	{
		memcpy( packet, recv_packet, MARKET_ITEM_SIZE );
		return MARKET_ITEM_UPDATED;
	}
	else if ( !strncmp( recv_packet, "page_items\0", 10 ) )
	{
		return MARKET_PAGE_ITEMS_GETED;
	}
	else if ( !strncmp( recv_packet, "market_is_empty\0", 15 ) )
	{
		return MARKET_IS_EMPTY;
	}
	else if( !strncmp( recv_packet, "item_info\0", 9 ) )
	{
		memcpy( packet, recv_packet, MARKET_ITEM_SIZE );
		return MARKET_ITEM_INFO;
	}
	else if ( !strncmp( recv_packet, "page_not_found\0", 14 ) )
	{
		return MARKET_PAGE_NOT_FOUND;
	}
	else if ( !strncmp( recv_packet, "del_item\0", 8 ) ) 
	{
		memcpy( packet, recv_packet, MARKET_ITEM_SIZE );
		return MARKET_ITEM_DELETED;
	}

	free_mem( recv_packet );
	return UNDEFINED_RET_CODE;
};

int connect_to_market( void )
{
	int fd = socket( AF_INET, SOCK_STREAM, 0 );

	if ( fd == -1 )
	{
		perror( "[-] Socket creation error!" );
		exit( SOCKET_CREATE_ERROR );
	}

	struct sockaddr_in address;
	memset( &address, 0, sizeof( address ) );

	address.sin_family = AF_INET;
	address.sin_port = htons( MARKET_PORT );
	address.sin_addr.s_addr = INADDR_ANY;

	int error = connect( fd, 
		(struct sockaddr *)&address, 
		sizeof( address ) 
	);

	if ( error == -1 )
	{
		perror( "[-] Market connection error!" );
		close( fd );
		return -1;
	}

	return fd;
};

int close_connection( int fd )
{
	return close( fd );
};

void remove_weapon_by_id( int id )
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

int remove_weapon( char* name, DWORD quality )
{
	if ( g_user->weapon_count == 0 )
	{
		puts( "[-] You don't have weapons!" );
		return -1;
	}

	int removed_id = -1;
	
	for ( int i = 0; g_user->weapons[ i ] != NULL; i++ )
	{
		if ( !strcmp( g_user->weapons[ i ]->name, name ) && 
			g_user->weapons[ i ]->quality == quality )
		{
			removed_id = i;
			break;
		}
	}

	if ( removed_id == -1 )
	{
		puts( "[-] Weapon not found!" );
		return -1;
	}
	else
	{
		g_user->weapon_count--;

		for ( int i = removed_id; g_user->weapons[ i ] != NULL; i++ )
		{
			g_user->weapons[ i ] = g_user->weapons[ i + 1 ];
		}
	}

	return TRUE;
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
	char* tmp_str = (char*) alloc_mem( strlen( part ) + 16 );
	strncpy( tmp_str, part, strlen( part ) );
	wp->quality = atoi( tmp_str );
	free_mem( tmp_str );

	// set name
	part = strtok( NULL, "|" );

	if ( part == NULL )
	{
		puts( "[-] Invalid weapon string!" );
		exit( INVALID_WEAPON_STRING );
	}
	
	tmp_str = (char*) alloc_mem( strlen( part ) + 16 );
	strncpy( tmp_str, part, strlen( part ) );
	wp->name = tmp_str;

	// set desc
	part = strtok( NULL, "|" );

	if ( part == NULL )
	{
		wp->description = NULL;
	}
	else
	{
		char* desc_str = (char*) alloc_mem( strlen( part ) + 16 );
		strncpy( desc_str, part, strlen( part ) );
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
			char* line_copy = (char*) alloc_mem( nbytes );
			strncpy( line_copy, line, nbytes );

			if ( line_copy[ nbytes - 1 ] == '\n' )
			{
				line_copy[ nbytes - 1 ] = '\0';
			}

			if ( strlen( line_copy ) != 0 )
			{
				lines[ lines_idx ] = line_copy;

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

	int tmp = 0;

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
	char buf[ 16 ];
	int nbytes = read( 0, buf, 16 );

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

void free_weapon( weapon* ptr )
{
	free_mem( ptr->name );
	free_mem( ptr->description );
	free_mem( ptr );
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
			 ( buf[ i ] >= '0' && buf[ i ] <= '9') ||
			 buf[ i ] == '=' )
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