<?php


namespace App\Http\Controllers;


use App\Library\AppStorage;
use App\Library\Renderer;
use App\Services\SyncService;
use App\Services\UserService;
use Illuminate\Http\Request;
use App\Library\HtmlBuilder;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\File;

class SyncController extends Controller
{

    /**
     * @var SyncService $syncService
     */
    private $syncService;
    /**
     * @var UserService
     */
    private $userService;

    public function __construct(SyncService $service, UserService $us)
    {
        $this->syncService = $service;
        $this->userService = $us;
    }

    public function addSync(Request $request)
    {
        $this->validate($request, [
            'capacity' => 'required|int|between:3,50',
            'title' => 'required|string|max:100',
            'description' => 'required|string|max:500',
            'image_url' => 'url',
            'image_params' => 'array',
            'image_base64' => 'string|max:204800|regex:/^data:image\/jpeg;base64,[A-Za-z0-9=+\/]+$/m',
        ]);

        $user = Auth::user();

        $title = $request->get('title');
        $desc = $request->get('description');
        $syncData = $this->syncService->addSync($user->id,
            $title,
            $desc,
            $request->get('capacity')
        );

        if (!$syncData) {
            return \response()->json(['error' => 'Failed to add sync. Try again.'])->setStatusCode(412);
        }

        $img = null;
        if ($request->get('image_url')) {
            $img = (new HtmlBuilder())
                ->image($request->get('image_url'), 'anime', $request->get('image_params'));
        }

        /** @var UploadedFile $uploadedImg */
        $uploadedImg = $request->get('image_base64');
        if ($uploadedImg) {
            $img = (new HtmlBuilder())
                ->image($request->get('image_base64'), 'anime', $request->get('image_params'));
        }

        $data = view('base_ticket', [
            'title' => $title,
            'description' => $desc,
            'img' => $img,
        ])->render();

        /** @var AppStorage $storage */
        $storage = app(AppStorage::class);

        file_put_contents($storage->templatePath($syncData['id']), $data);
        return response()->json(['id' => $syncData['id']]);
    }

    public function getInfo($id)
    {
        $sync = $this->syncService->getSyncById($id);
        if (!$sync) {
            return response()->json(['error' => "Sync not found"])->setStatusCode(404);
        }
        $author = $this->userService->get($sync->author_id);
        return response()->json(
            ['id' => $sync->id,
                'capacity' => $sync->capacity,
                'title' => $sync->title,
                'description' => $sync->description,
                'author' => [
                    'id' => $author->id,
                    'email' => $author->email,
                ],
                'created_at' => $sync->created_at,
            ]
        );
    }

    public function list(Request $request)
    {
        $user = Auth::user();
        return response()->json($this->syncService->getUserSyncs($user->id));
    }

    public function get($id)
    {
        $user = Auth::user();
        $sync = $this->syncService->getSyncById($id);
        if (!$sync) {
            return response()->json(['error' => "Sync not found"])->setStatusCode(404);
        }
        if ($sync->author_id != $user->id) {
            return response()->json(['error' => "Unauthorized"])->setStatusCode(403);
        }
        return response()->json($this->syncService->listMembers($sync->id));
    }

    public function addMember($id)
    {
        $sync = $this->syncService->getSyncById($id);
        if (!$sync) {
            return response()->json(['error' => "Sync not found"])->setStatusCode(404);
        }
        $this->validate(\request(), [
            'nickname' => 'required|string|between:3,50',
        ]);
        $nickname = \request('nickname');
        $data = $this->syncService->addMember($sync, $nickname);
        if (!$data) {
            return \response()->json(['error' => 'Failed to add member. Try again later.'])->setStatusCode(503);
        }

        /** @var AppStorage $storage */
        $storage = app(AppStorage::class);

        $template = $storage->templatePath($sync->id);
        if (!file_exists($template)) {
            return \response()->json(['error' => 'Failed to find sync template.'])->setStatusCode(503);
        }

        $templateData = file_get_contents($template);

        $templateData = str_replace("##NICKNAME##", (new HtmlBuilder())->text($nickname), $templateData);

        $tempFile = tempnam('/tmp', "TICKET_HTML") . ".html";

        file_put_contents($tempFile, $templateData);

        $public_id = $data['public_id'];

        $ticketFile = $storage->ticketPath($public_id);

        /** @var Renderer $renderer */
        $renderer = app(Renderer::class);

        $msg = $renderer->render($tempFile, $ticketFile);

        unlink($tempFile);

        return \response()->json(['public_id' => $public_id, 'message' => $msg, 'ticket_url' => '/tickets/' . $public_id . '.pdf']);
    }

    public function ticket($id)
    {
        $info = $this->syncService->getTicketInfo($id);
        if (!$info) {
            return response()->json(['error' => "Sync not found"])->setStatusCode(404);
        }
        $publicId = $info->public_id;
        $syncId = $info->sync_id;
        $sync = $this->syncService->getSyncById($syncId);
        $syncData = [
            'title' => $sync->title,
            'description' => $sync->description,
        ];
        return response()->json([
                'sync' => $syncData, 'nickname' => $info->nickname, 'public_id' => $publicId,
                'ticket_url' => '/tickets/' . $publicId . '.pdf']
        );
    }

    public function latestSyncs()
    {
        return response()->json($this->syncService->latestSyncs());
    }
}
