<?php

namespace App\Jobs;

use App\Library\AppStorage;
use App\Library\HtmlBuilder;
use App\Library\Renderer;

class RendererJob extends Job
{
    protected $templatePath;
    protected $nickName;
    protected $publicId;

    public function __construct($templatePath, $nickName, $publicId)
    {
        $this->templatePath = $templatePath;
        $this->nickName = $nickName;
        $this->publicId = $publicId;
    }

    /**
     * Execute the job.
     *
     * @return void
     */
    public function handle()
    {
        $templateData = file_get_contents($this->templatePath);

        $templateData = str_replace("##NICKNAME##", (new HtmlBuilder())->text($this->nickName), $templateData);

        $tempFile = tempnam('/tmp', "TICKET_HTML") . ".html";

        file_put_contents($tempFile, $templateData);

        /** @var AppStorage $storage */
        $storage = app(AppStorage::class);

        $ticketFile = $storage->ticketPath($this->publicId);

        /** @var Renderer $renderer */
        $renderer = app(Renderer::class);

        $renderer->render($tempFile, $ticketFile);

        unlink($tempFile);
    }
}
