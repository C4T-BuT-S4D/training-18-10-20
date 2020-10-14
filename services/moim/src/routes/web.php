<?php

/** @var \Laravel\Lumen\Routing\Router $router */

/*
|--------------------------------------------------------------------------
| Application Routes
|--------------------------------------------------------------------------
|
| Here is where you can register all of the routes for an application.
| It is a breeze. Simply tell Lumen the URIs it should respond to
| and give it the Closure to call when that URI is requested.
|
*/

$router->get('/', function () use ($router) {
    return $router->app->version();
});

$router->post('/api/register', 'AuthController@register');
$router->post('/api/login', 'AuthController@login');
$router->post('/api/sync/{id}/join', 'SyncController@addMember');
$router->get('/api/ticket/{id}', 'SyncController@ticket');
$router->get('/api/syncs', 'SyncController@latestSyncs');

$router->group(['middleware' => ['auth:api']], function () use ($router) {
    $router->get('/api/sync', 'SyncController@list');
    $router->post('/api/sync', 'SyncController@addSync');
    $router->get('/api/sync/{id}', 'SyncController@get');
});
