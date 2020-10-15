<?php


namespace App\Services;


use Illuminate\Auth\GenericUser;
use Illuminate\Support\Facades\DB;

class UserService
{
    const table = 'users';

    public function exists($email)
    {
        return DB::table(self::table)->where('email', $email)->first() != null;
    }

    public function get($id) {
        return DB::table(self::table)->where('id', $id)->first();
    }

    public function addUser($email, $password)
    {
        $password = hash('sha256', $password);
        $ok = DB::table(self::table)->insert(['email' => $email, 'password' => $password]);
        if (!$ok) {
            return null;
        }
        return new GenericUser(['email' => $email, 'id' => $rowId = DB::connection()->getPdo()->lastInsertId()]);
    }

    public function findUser($email, $password)
    {
        $password = hash('sha256', $password);
        $rows = DB::table(self::table)->where(['email' => $email, 'password' => $password])->first();
        if ($rows) {
            return new GenericUser(['email' => $rows->email, 'id' => $rows->id]);
        }
        return null;
    }
}
