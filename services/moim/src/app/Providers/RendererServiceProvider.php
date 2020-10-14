<?php


namespace App\Providers;


use App\Library\Renderer;
use Carbon\Laravel\ServiceProvider;

class RendererServiceProvider extends ServiceProvider
{
    public function register()
    {
        $this->app->singleton(Renderer::class, function ($app) {
            return new Renderer('/usr/bin/phantomjs');
        });
    }
}
