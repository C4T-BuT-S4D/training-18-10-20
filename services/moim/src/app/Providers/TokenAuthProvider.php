<?php


namespace App\Providers;


use App\Library\TokenAuthentication;
use Carbon\Laravel\ServiceProvider;

class TokenAuthProvider extends ServiceProvider
{
    public function register()
    {
        $this->app->singleton(TokenAuthentication::class, function ($app) {
            return new TokenAuthentication(env('TOKEN_KEY'));
        });
    }
}
