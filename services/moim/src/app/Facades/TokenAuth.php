<?php


namespace App\Facades;

use App\Library\TokenAuthentication;

use Illuminate\Support\Facades\Facade;

class TokenAuth extends Facade
{
    protected static function getFacadeAccessor()
    {
        return TokenAuthentication::class;
    }
}
