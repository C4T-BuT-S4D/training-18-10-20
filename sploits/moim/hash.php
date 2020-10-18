<?php

$file = $argv[1];
$key = $argv[2];

$data = file_get_contents($file);

echo hash_hmac('haval160,4', $data, $key);
