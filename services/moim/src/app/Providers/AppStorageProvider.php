<?php


namespace App\Providers;


use App\Library\AppStorage;
use Carbon\Laravel\ServiceProvider;

class AppStorageProvider extends ServiceProvider
{
    public function register()
    {
        $this->app->singleton(AppStorage::class, function ($app) {
            return new AppStorage(env('STORAGE_BASE_PATH'));
        });
    }
}
