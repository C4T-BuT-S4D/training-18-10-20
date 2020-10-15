<?php


namespace App\Library;


class AppStorage
{
    const templatesDir = 'templates';
    const ticketsDir = 'tickets';
    /**
     * @var string
     */
    private $ticketBase;
    /**
     * @var string
     */
    private $templatesBase;

    private function join($d1, $d2)
    {
        if (substr_compare($d1, "/", -1) === 0) {
            $d1 = substr($d1, 0, strlen($d1) - 1);
        }
        if (substr_compare($d2, "/", 0, 1) === 0) {
            $d2 = substr($d2, 1);
        }
        return "{$d1}/{$d2}";
    }

    public function __construct($baseFolder)
    {
        $this->ticketBase = $this->join($baseFolder, self::ticketsDir);
        $this->templatesBase = $this->join($baseFolder, self::templatesDir);
        if (!file_exists($this->ticketBase)) {
            mkdir($this->ticketBase, 0777, true);
        }
        if (!file_exists($this->templatesBase)) {
            mkdir($this->templatesBase, 0777, true);
        }
    }

    public function templatePath($id)
    {
        return $this->join($this->templatesBase, strval($id) . '.html');
    }

    public function ticketPath($id)
    {
        return $this->join($this->ticketBase, $id . '.pdf');
    }
}
