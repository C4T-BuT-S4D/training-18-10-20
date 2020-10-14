<?php


namespace App\Services;


use Illuminate\Support\Facades\DB;
use Ramsey\Uuid\Uuid;

class SyncService
{
    const table = 'anime_syncs';
    const membersTable = 'sync_members';

    public function addSync($userId, $title, $description, $capacity)
    {
        $ok = DB::table(self::table)->insert([
            'author_id' => $userId,
            'title' => $title,
            'description' => $description,
            'capacity' => $capacity
        ]);
        if ($ok) {
            return ['id' => $rowId = DB::connection()->getPdo()->lastInsertId()];
        }
        return null;
    }

    public function getSyncById($syncId)
    {
        return DB::table(self::table)->where('id', $syncId)->first();
    }

    public function getUserSyncs($userId)
    {
        return DB::table(self::table)->where('author_id', $userId)->get();
    }

    public function latestSyncs()
    {
        return DB::table(self::table)->orderBy('id', 'DESC')->limit(75)->get();
    }

    public function addMember($sync, $nickname)
    {
        if ($sync->capacity - 1 >= 0) {
            DB::table(self::table)->where('id', $sync->id)->update(['capacity' => $sync->capacity - 1]);
        } else {
            throw new \Exception('Sync capacity is reached');
        }
        $publicId = Uuid::uuid4()->toString();
        $ok = DB::table(self::membersTable)->insert([
            'sync_id' => $sync->id,
            'public_id' => $publicId,
            'nickname' => $nickname,
        ]);
        if (!$ok) {
            return null;
        }
        return ['public_id' => $publicId];
    }

    public function listMembers($syncId)
    {
        return DB::table(self::membersTable)->where('sync_id', $syncId)->get();
    }

    public function getTicketInfo($remoteId)
    {
        return DB::table(self::membersTable)->where('public_id', $remoteId)->first();
    }

}
