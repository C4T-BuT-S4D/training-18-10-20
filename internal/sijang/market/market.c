#include "market.h"


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

	int errcode = bind( server_fd, (struct sockaddr *)&address, sizeof( address ) );

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

	return 0;
};

void setup( void )
{
	setvbuf( stdin,  0, 2, 0 );
	setvbuf( stdout, 0, 2, 0 );
	setvbuf( stderr, 0, 2, 0 );

	//market_load();
};