<?php


namespace App\Http\Controllers;


use App\Facades\TokenAuth;
use App\Services\UserService;
use Illuminate\Http\Request;

class AuthController extends Controller
{
    /**
     * @var UserService $userService
     */
    private $userService;

    public function __construct(UserService $userService)
    {
        $this->userService = $userService;
    }

    public function login(Request $request)
    {
        $this->validate($request, [
            'email' => 'required|email',
            'password' => 'required',
        ]);
        $user = $this->userService->findUser($request->get('email'), $request->get('password'));
        if ($user) {
            return \response()->json(['status' => 'ok', 'user' => ['id' => $user->id, 'email' => $user->email]])
                ->withCookie(TokenAuth::cookie($user));
        }
        return \response()->json(['error' => 'Login or password incorrect.'], 412);
    }


    public function register(Request $request)
    {
        $this->validate($request, [
            'email' => 'required|email',
            'password' => 'required',
        ]);


        $email = $request->get('email');
        $password = $request->get('password');


        if ($this->userService->exists($email)) {
            return \response()->json(['error' => 'User with this email already exists.'], 412);
        }

        $user = $this->userService->addUser($email, $password);
        if ($user == null) {
            return \response()->json(['error' => 'Failed to register. Try again.'], 412);
        }

        return \response()->json(['status' => 'ok', 'user' => ['id' => $user->id, 'email' => $user->email]])
            ->withCookie(TokenAuth::cookie($user));
    }
}
