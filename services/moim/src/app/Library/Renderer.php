<?php


namespace App\Library;


class Renderer
{
    private $rendererPath;
    const timeout = 2;

    public function __construct($rendererPath)
    {
        $this->rendererPath = $rendererPath;
    }

    public function render($inputPath, $outputPath)
    {
        $timeout = self::timeout;
        $scriptPath = resource_path('scripts') . '/renderer.js';
        $cmd = "timeout {$timeout} {$this->rendererPath} {$scriptPath} {$inputPath} {$outputPath}";
        return exec($cmd);
    }
}
