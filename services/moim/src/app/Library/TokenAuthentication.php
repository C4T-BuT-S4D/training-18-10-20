<?php


namespace App\Library;

use Exception;
use Illuminate\Auth\GenericUser;
use Symfony\Component\HttpFoundation\Cookie;
use MessagePack\MessagePack;

class InvalidTokenException extends Exception
{
}


class TokenAuthentication
{
    private $key;

    public function cookieName()
    {
        return 'session_token';
    }

    public function __construct($key)
    {
        $this->key = $key;
    }

    private function hsh($data)
    {
        return hash_hmac('haval160,4', $data, $this->key);
    }

    public function token($data)
    {
        $packed = MessagePack::pack($data);
        return MessagePack::pack([$packed, $this->hsh($packed)]);
    }

    public function decode($data)
    {
        $unpacked = MessagePack::unpack($data);
        if (count($unpacked) != 2) {
            throw new InvalidTokenException("Invalid array length");
        }

        if ($this->hsh($unpacked[0]) !== $unpacked[1]) {
            throw new InvalidTokenException("Invalid hash");
        }
        return MessagePack::unpack($unpacked[0]);
    }

    public function cookie(GenericUser $user)
    {
        return Cookie::create($this->cookieName(), $this->token(['id' => $user->id, 'email' => $user->email]));
    }

    public function fromCookie($cookie)
    {
        $data = $this->decode($cookie);
        if ($data) {
            return new GenericUser(['id' => $data['id'], 'email' => $data['email']]);
        }
        return null;
    }
}
