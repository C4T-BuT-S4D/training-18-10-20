<?php


namespace App\Services;


use Illuminate\Support\Facades\DB;

class ChallengesService
{
    const max = 10000;
    const table = 'challenges';

    public function generate($user_id)
    {
        $randInt = rand(1, self::max - 1);
        $c = str_pad(strval($randInt), 4, '0', STR_PAD_LEFT);
        if (DB::table(self::table)->upsert(['user_id' => $user_id, 'challenge' => $c], 'user_id', ['challenge'])) {
            return $c;
        }
        return null;
    }

    public function revoke($user_id)
    {
        DB::table(self::table)->where('user_id', $user_id)->delete();
    }

    public function find($user_id)
    {
        return DB::table(self::table)->where('user_id', $user_id)->first();
    }

    public function validate($user_id, $answer)
    {
        $challenge = $this->find($user_id);
        if (!$challenge) {
            throw new \Exception("Challenge not found");
        }
        $this->revoke($user_id);
        return substr(hash('sha256', $challenge->challenge . $answer), 0, 5) == '00000';
    }

}
