#include "market.h"


pthread_mutex_t market_mutex;

int main()
{
	setup();
	SOCKET server_fd = socket( AF_INET, SOCK_STREAM, 0);

	if ( server_fd == -1 ) 
	{
		perror( "[-] Socket creation error!" );
		exit( ERROR_SOCKET_CREATE );
	}

	struct sockaddr_in address;
	memset( &address, 0, sizeof( address ) );

	address.sin_family = AF_INET;
	address.sin_port = htons( MARKET_PORT );
	address.sin_addr.s_addr = INADDR_ANY;

	int errcode = bind( server_fd, (struct sockaddr *)&address, 
		sizeof( address ) );

	if ( errcode == -1 ) 
	{
		perror( "[-] Socket bind error!" );
		exit( ERROR_SOCKET_BIND );
	}

	errcode = listen( server_fd, LISTEN_CNT );

	if ( errcode == -1 )
	{
		perror( "[-] Socket listen error!" );
		exit( ERROR_SOCKET_LISTEN );
	}

	while ( TRUE ) 
	{
		struct sockaddr_in client_address;
		socklen_t addr_len = sizeof( client_address );

		SOCKET client_fd = accept( server_fd, 
			(struct sockaddr *)&client_address, &addr_len );

		if ( client_fd == -1 ) 
		{
			perror( "[-] Some error in accept!" );
			continue;
		}

		// create thread to connection

		pthread_t tid;
		pthread_attr_t attr;

		pthread_attr_init( &attr );
		thread_args* args = (thread_args*) malloc( sizeof( thread_args ) );
		args->client_fd = client_fd;

		if ( pthread_create( &tid, &attr, pthread_routine, (void *)args ) != 0 ) 
		{
			perror( "pthread_create" );
			free( args );
			continue;
		}

		pthread_detach( tid );
	}

	return 0;
};

void setup( void )
{
	setvbuf( stdin,  0, 2, 0 );
	setvbuf( stdout, 0, 2, 0 );
	setvbuf( stderr, 0, 2, 0 );

	pthread_mutex_init( &market_mutex, NULL );
	market_init();
};

void* pthread_routine( void *args )
{
	thread_args* l_args = (thread_args*) args;
	SOCKET client_fd = l_args->client_fd;

	// set socket timeout
	struct timeval tv;
	tv.tv_sec = RECV_TIMEOUT;
	tv.tv_usec = 0;

	setsockopt( client_fd, SOL_SOCKET, SO_RCVTIMEO, (const char*) &tv, sizeof( tv ) );
	setsockopt( client_fd, SOL_SOCKET, SO_SNDTIMEO, (const char*) &tv, sizeof( tv ) );
	
	char* packet = (char*) malloc( REQ_TO_ADD_PACKET_SIZE + 16 );

	while ( TRUE )
	{	
		memset( packet, 0, REQ_TO_ADD_PACKET_SIZE );
		int nbytes = recv( client_fd, packet, REQ_TO_ADD_PACKET_SIZE, 0 );
		//printf( "first packet = %s\n", packet );

		if ( nbytes <= 0 )
		{	
			free( packet );
			perror( "[-] No data received!" );
			pthread_exit( NULL );
		}

		char* ptr = strtok( packet, "|" );
		ptr = strtok( NULL, "|" );
		enum COMMANDS cmd = get_cmd_by_name( ptr );

		// try to lock mutex
		if ( pthread_mutex_lock( &market_mutex ) == 0 )
		{
			char* req_packet = (char*) malloc( ACCESS_PACKET_SIZE + 16 );
			memset( req_packet, 0, ACCESS_PACKET_SIZE );
			strcpy( req_packet, "access" );

			nbytes = send( client_fd, req_packet, ACCESS_PACKET_SIZE, 0 );

			if ( nbytes != ACCESS_PACKET_SIZE )
			{
				printf( "[-] Some problems in data send to client!" );
				close( client_fd );
				pthread_exit( NULL );
			}

			free( req_packet );

			// get data from client
			char* second_packet = (char*) malloc( MARKET_ITEM_SIZE + 16 );
			memset( second_packet, 0, MARKET_ITEM_SIZE );
			
			nbytes = recv( client_fd, second_packet, MARKET_ITEM_SIZE, 0 );
			//printf( "second_packet = %s\n", second_packet );

			if ( nbytes <= 0 )
			{
				nbytes = recv( client_fd, second_packet, MARKET_ITEM_SIZE, 0 );
				printf( "[-] Empty data from client!" );
				pthread_mutex_unlock( &market_mutex );
				pthread_exit( NULL );
			}

			proceed_packet( cmd, second_packet, client_fd );
			pthread_mutex_unlock( &market_mutex );
			break;
		}
		else
		{
			char* req_packet = (char*) malloc( BUSY_PACKET_SIZE + 16 );
			memset( req_packet, 0, BUSY_PACKET_SIZE );
			strcpy( req_packet, "busy" );

			nbytes = send( client_fd, req_packet, BUSY_PACKET_SIZE, 0 );

			if ( nbytes != BUSY_PACKET_SIZE )
			{
				free( req_packet );
				printf( "[-] Some problems in data send to client!" );
				close( client_fd );
				pthread_exit( NULL );
			}

			free( req_packet );
			usleep( SLEEP_TIME );
		}
	}

	free( packet );
	close( client_fd );
	pthread_exit( NULL );

	return NULL;
};

enum COMMANDS get_cmd_by_name( char* name )
{
	if ( !strncmp( name, "add_item", 8 ) )
	{
		return ADD_ITEM;
	}
	else if ( !strncmp( name, "del_item", 8 ) )
	{
		return DEL_ITEM;
	}
	else if ( !strncmp( name, "get_page", 8 ) )
	{
		return GET_PAGE;
	}
	else if ( !strncmp( name, "view_items", 10 ) )
	{
		return VIEW_ITEMS;
	}
	else if ( !strncmp( name, "change_status", 13 ) )
	{
		return CHANGE_STATUS;
	}
	else if ( !strncmp( name, "full_item_info", 14 ) )
	{
		return FULL_ITEM_INFO;
	}
	else if ( !strncmp( name, "update", 6 ) )
	{
		return UPDATE_ITEM;
	}
	else if ( !strncmp( name, "item_info", 9 ) )
	{
		return ITEM_INFO;
	}
	else
	{
		printf( "[-] Cmd: %s\n", name );
		perror( "[-] Undefined command!" );
		return UNDEF_CMD;
	}

	return UNDEF_CMD;
};

int market_init( void )
{
	int fd = open( MARKET_PATH, O_RDWR | O_CREAT, (mode_t)0600 );

	if ( fd == -1 )
	{
		perror( "[-] Error in market open file!" );
		exit( MARKET_OPEN_ERROR );
	}

	// wtf ???
	lseek( fd, MARKET_MAX_SIZE - 1, SEEK_SET );
	write( fd, "", 1 );

	g_market = (market_header*) mmap( (void*) MARKET_BASE_ADDR, MARKET_MAX_SIZE, 
		PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0 
	);

	if ( g_market == NULL )
	{
		perror( "[-] Error in market mapping!" );
		exit( MARKET_MAPPING_ERROR );
	}

	return 0;
};

int proceed_packet( enum COMMANDS cmd, char* packet, int client_fd )
{
	if ( cmd == UNDEF_CMD )
	{
		return UNDEF_CMD;
	}

	switch ( cmd )
	{
		case ADD_ITEM:
			add_item( packet, client_fd );
			break;
		case DEL_ITEM:
			del_item( packet, client_fd );
			break;
		case VIEW_ITEMS:
			view_items( packet );
			break;
		case CHANGE_STATUS:
			change_status( packet );
			break;
		case FULL_ITEM_INFO:
			full_item_info( packet, client_fd );
			break;
		case UPDATE_ITEM:
			update_item( packet, client_fd );
			break;
		case GET_PAGE:
			get_page( packet, client_fd );
			break;
		case ITEM_INFO:
			item_info( packet, client_fd );
			break;
		default:
			return 1;
	}

	return 0;
};

int item_info( char* packet, int client_fd )
{
	char* ptr = strtok( packet, "|" ); // get magic
	ptr = strtok( NULL, "|" ); // get token

	DWORD f_token = atoi( ptr );

	market_item* item = find_item_by_token( f_token );

	if ( item == NULL )
	{
		// no such item
		item_not_found( client_fd );
		return ITEM_NOT_FOUND;
	}

	send_item_info( client_fd, item );

	return 0;
};

int get_page( char* packet, int client_fd )
{
	char* ptr = strtok( packet, "|" );

	int page_idx = 0;
	int one_page_count = 10;

	ptr = strtok( NULL, "|" );
	page_idx = atoi( ptr );

	ptr = strtok( NULL, "|" );
	one_page_count = atoi( ptr );

	if ( g_market->count_of_items == 0 )
	{
		market_is_empty( client_fd );
		return MARKET_IS_EMPTY;
	}

	char* req_packet = (char*) malloc( (sizeof( market_item ) * one_page_count) + 64 );
	memset( req_packet, 0, (sizeof( market_item ) * one_page_count) + 64 );

	int items_cnt = 0;

	int offset = 0;

	if ( g_market->max_item_id > 10 && page_idx > 0 )
	{
		if ( (g_market->max_item_id / 10) < page_idx )
		{
			page_not_found( client_fd );
			return 0;
		}
		else
		{
			offset = page_idx;
		}
	}

	for ( int i = (g_market->max_item_id - (offset * 10)); i >= 0 && items_cnt < 10; i-- )
	{
		if ( !g_market->chunks[ i ].used )
			continue;
		
		if ( g_market->chunks[ i ].is_archived )
			continue;

		market_item* itm = &g_market->chunks[ i ];
		//printf( "item[%d]\n", i );

		if ( itm->name != NULL && itm->cost != 0 && itm->token != 0 )
		{
			sprintf( req_packet + strlen( req_packet ),
				"item|%s|%d|%u|\n",
				itm->name, itm->cost, itm->token
			);

			items_cnt += 1;
		}
	}

	if ( items_cnt == 0 )
	{
		market_is_empty( client_fd );
		return MARKET_IS_EMPTY;
	}

	send( client_fd, "page_items\0", 10, 0 );
	usleep( 500 );
	
	//printf( "get_page, req_packet = %s\n", req_packet );

	send( client_fd, req_packet, strlen( req_packet ), 0 );

	return 0;
};

int update_item( char* packet, int client_fd )
{
	char* ptr = strtok( packet, "|" );

	for ( int i = 0; i < 6; i++ ) // skip to archived
	{
		ptr = strtok( NULL, "|" );
	}

	BYTE new_archived_value = atoi( ptr );
	ptr = strtok( NULL, "|" ); // get token
	DWORD token = atoi( ptr );

	market_item* item = find_item_by_token( token );

	if ( item == NULL )
	{
		item_not_found( client_fd ); 
	}

	item->is_archived = new_archived_value;
	msync( g_market, MARKET_MAX_SIZE, MS_SYNC );
	item_updated( client_fd );

	return 0;
};

int add_item( char* packet, int client_fd )
{
	char* ptr = strtok( packet, "|" );

	// check free space
	int free_space = MARKET_MAX_SIZE - ( g_market->count_of_items * sizeof( market_item ) );

	if ( free_space <= 0 )
	{
		printf( "[-] No available space to add item!" );
		char* packet = (char*) malloc( 64 );
		memset( packet, 0, 64 );

		strcpy( packet, "item_not_added" );
		int packet_size = strlen( packet );

		int nbytes = send( client_fd, packet, packet_size, 0 );

		if ( nbytes != packet_size )
		{
			printf( "[-] Some error in clinet send!" );
			return SENDING_ERROR;
		}

		return NO_FREE_SPACE;
	}

	// find first free entry
	int new_item_idx = find_free_entry();

	if ( new_item_idx == -1 )
	{	
		char* packet = (char*) malloc( 64 );
		memset( packet, 0, 64 );

		strcpy( packet, "item_not_added" );
		int packet_size = strlen( packet );

		int nbytes = send( client_fd, packet, packet_size, 0 );

		if ( nbytes != packet_size )
		{
			printf( "[-] Some error in clinet send!" );
			return SENDING_ERROR;
		}

		printf( "[-] Cant find any free entry!" );
		return NO_FREE_SPACE;
	}

	if ( new_item_idx > g_market->max_item_id )
	{
		g_market->max_item_id = new_item_idx;
	}

	g_market->count_of_items += 1;
	g_market->chunks[ new_item_idx ].used = TRUE;

	// copy name to struct
	ptr = strtok( NULL, "|" );

	if ( ptr == NULL )
	{
		//printf( "SISGEV!!!, PACKET: %s\n", packet );
		return SENDING_ERROR;
	}

	strcpy( g_market->chunks[ new_item_idx ].name, ptr );

	// copy description to struct
	ptr = strtok( NULL, "|" );
	if ( ptr == NULL )
	{
		//printf( "SISGEV!!!, PACKET: %s\n", packet );
		return SENDING_ERROR;
	}

	strcpy( g_market->chunks[ new_item_idx ].description, ptr );

	// copy cost to struct
	ptr = strtok( NULL, "|" );
	if ( ptr == NULL )
	{
		//printf( "SISGEV!!!, PACKET: %s\n", packet );
		return SENDING_ERROR;
	}

	g_market->chunks[ new_item_idx ].cost = atoi( ptr );

	// copy quality to struct
	ptr = strtok( NULL, "|" );
	if ( ptr == NULL )
	{
		//printf( "SISGEV!!!, PACKET: %s\n", packet );
		return SENDING_ERROR;
	}

	g_market->chunks[ new_item_idx ].quality = atoi( ptr );

	// copy owner to struct
	ptr = strtok( NULL, "|" );
	if ( ptr == NULL )
	{
		//printf( "SISGEV!!!, PACKET: %s\n", packet );
		return SENDING_ERROR;
	}

	strcpy( g_market->chunks[ new_item_idx ].owner, ptr );

	// set is archived
	ptr = strtok( NULL, "|" );
	if ( ptr == NULL )
	{
		//printf( "SISGEV!!!, PACKET: %s\n", packet );
		return SENDING_ERROR;
	}

	if ( atoi( ptr ) == 1 )
		g_market->chunks[ new_item_idx ].is_archived = TRUE;
	else
		g_market->chunks[ new_item_idx ].is_archived = FALSE;

	// set token
	ptr = strtok( NULL, "|" );
	g_market->chunks[ new_item_idx ].token = atoi( ptr );

	// copy password
	ptr = strtok( NULL, "|" );

	if ( ptr == NULL )
	{
		//printf( "SISGEV!!!, PACKET: %s\n", packet );
		return SENDING_ERROR;	
	}

	strcpy( g_market->chunks[ new_item_idx ].password, ptr );

	// update file on FS
	msync( (void*)g_market, MARKET_MAX_SIZE, MS_SYNC );

	// send correct code
	char* s_packet = (char*) malloc( 64 );
	memset( s_packet, 0, 64 );

	strcpy( s_packet, "item_added" );
	int packet_size = strlen( s_packet );

	int nbytes = send( client_fd, s_packet, packet_size, 0 );

	if ( nbytes != packet_size )
	{
		printf( "[-] Some error in clinet send!" );
		free( s_packet );
		return SENDING_ERROR;
	}

	free( s_packet );

	return ITEM_ADDED;
};

int full_item_info( char* packet, int client_fd )
{	
	char* ptr = strtok( packet, "|" ); // get magic
	ptr = strtok( NULL, "|" ); // get token

	if ( ptr == NULL )
	{
		item_not_found( client_fd );
		return ITEM_NOT_FOUND;
	}

	DWORD f_token = atoi( ptr );

	market_item* item = find_item_by_token( f_token );

	if ( item == NULL )
	{
		// no such item
		item_not_found( client_fd );
		return ITEM_NOT_FOUND;
	}

	// check owner and password
	ptr = strtok( NULL, "|" ); // get username

	if ( ptr == NULL )
	{
		item_not_found( client_fd );
		return ITEM_NOT_FOUND;
	}

	if ( strcmp( ptr, item->owner ) )
	{
		access_denied( client_fd );
		return ITEM_ACCESS_DENIED;
	}

	ptr = strtok( NULL, "|" ); // get password

	if ( ptr == NULL )
	{
		item_not_found( client_fd );
		return ITEM_NOT_FOUND;
	}

	if ( strcmp( ptr, item->password ) )
	{
		access_denied( client_fd );
		return ITEM_ACCESS_DENIED;
	}

	send_full_item_info( item, client_fd );

	return 0;
};

void send_item_info( int client_fd, market_item* item )
{
	char* packet = (char*) malloc( MARKET_ITEM_SIZE + 32 );
	memset( packet, 0, MARKET_ITEM_SIZE );

	sprintf( packet, "item_info|%s|%d|%d|%s|%d|%u|", 
		item->name, item->cost, item->quality, item->owner, 
		item->is_archived, item->token
	);

	send( client_fd, packet, strlen( packet ), 0 );
	free( packet );
};

void send_full_item_info( market_item* item, int client_fd )
{
	char* packet = (char*) malloc( MARKET_ITEM_SIZE + 32 );
	memset( packet, 0, MARKET_ITEM_SIZE );

	sprintf( packet, "full_item_info|%s|%s|%d|%d|%s|%d|%u|%s|", 
		item->name, item->description, item->cost, item->quality, 
		item->owner, item->is_archived, item->token, item->password 
	);

	send( client_fd, packet, strlen( packet ), 0 );
	free( packet );
};

void page_not_found( int client_fd )
{
	char* packet = (char*) malloc( MARKET_ITEM_SIZE + 32 );
	memset( packet, 0, MARKET_ITEM_SIZE );
	strcpy( packet, "page_not_found" );

	send( client_fd, packet, strlen( packet ), 0 );
	free( packet );
};

void market_is_empty( int client_fd )
{
	char* packet = (char*) malloc( MARKET_ITEM_SIZE + 32 );
	memset( packet, 0, MARKET_ITEM_SIZE );
	strcpy( packet, "market_is_empty" );

	send( client_fd, packet, strlen( packet ), 0 );
	free( packet );
};

void item_updated( int client_fd )
{

	char* packet = (char*) malloc( MARKET_ITEM_SIZE + 32 );
	memset( packet, 0, MARKET_ITEM_SIZE );
	strcpy( packet, "item_updated" );

	send( client_fd, packet, strlen( packet ), 0 );
	free( packet );
};

void access_denied( int client_fd )
{
	char* packet = (char*) malloc( MARKET_ITEM_SIZE + 32 );
	memset( packet, 0, MARKET_ITEM_SIZE );

	strcpy( packet, "access_denied" );

	send( client_fd, packet, strlen( packet ), 0 );
	free( packet );
};

void item_not_found( int client_fd )
{
	char* packet = (char*) malloc( MARKET_ITEM_SIZE + 32);
	memset( packet, 0, MARKET_ITEM_SIZE );

	strcpy( packet, "item_not_found" );

	send( client_fd, packet, strlen( packet ), 0 );
	free( packet );
};

int del_item( char* packet, int client_fd )
{	
	char* ptr = strtok( packet, "|" ); // get magic
	ptr = strtok( NULL, "|" ); // get token

	DWORD f_token = atoi( ptr );

	int idx = find_item_idx_by_token( f_token );

	if ( idx == -1 )
	{
		// no such item
		item_not_found( client_fd );
		return ITEM_NOT_FOUND;
	}

	market_item* item = &g_market->chunks[ idx ];
	send_full_item_info( item, client_fd );

	// check if item archived
	// cant delete archived item
	if ( item->is_archived )
	{
		return 0;
	}

	// delete item 
	if ( idx == g_market->max_item_id && idx != 0 )
		g_market->max_item_id -= 1;
	
	g_market->count_of_items -= 1;

	memset( &g_market->chunks[ idx ], 0, sizeof( market_item ) );
	g_market->chunks[ idx ].used = FALSE;

	msync( g_market, MARKET_MAX_SIZE, MS_SYNC );
	return 0;
};

int view_items( char* packet )
{
	return 0;
};

int change_status( char* packet )
{
	return 0;
};

int find_free_entry( void )
{
	for ( int i = 0; i < MAX_ITEMS_COUNT; i++ )
	{
		if ( !g_market->chunks[ i ].used )
		{
			return i;
		}
	}

	return -1;
};

market_item* find_item_by_token( DWORD token )
{
	for ( int i = 0; i < g_market->max_item_id + 1; i++ )
	{
		if ( g_market->chunks[ i ].used )
		{
			if ( g_market->chunks[ i ].token == token )
			{
				return &g_market->chunks[ i ];
			}
		}
	}

	return NULL;
};

int find_item_idx_by_token( DWORD token )
{
	for ( int i = 0; i < g_market->max_item_id + 1; i++ )
	{
		if ( g_market->chunks[ i ].used )
		{
			if ( g_market->chunks[ i ].token == token )
				return i;
		}
	}

	return -1;
}