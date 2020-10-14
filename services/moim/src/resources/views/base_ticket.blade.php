<html lang="en">
<head>
    <meta charset="utf-8">
    <style>
        @page {
            size: A4;
            margin: 0;
            padding: 0;
        }

        body {
            margin: 0;
            font-family: "Audiowide", cursive;
            font-weight: 400;
            font-size: 23px;
        }

        #top-bar {
            border-bottom: 1px solid #7C7C7C;
            padding: 1cm 0 10px;
            background-repeat: no-repeat;
            background: rgb(238, 174, 202);
            background: radial-gradient(circle, rgba(238, 174, 202, 1) 0%, rgba(148, 187, 233, 1) 100%);
            overflow: hidden;
        }

        #top-bar p {
            float: left;
        }

        #top-bar img {
            float: right;
        }

        #event {
            font-weight: 700;
            font-size: 1.5em;
            line-height: 10%;
            text-transform: uppercase;
        }

    </style>
    <title>Ticket</title>
</head>
<body>
<div id="top-bar">
    <div id="event"><p>{{ $title }}</p></div>
    <div id="title"><p>For: ##NICKNAME##</p></div>
    <div id="info"><p>{{ $description }}</p></div>
    <div id="logo">
        {{ $img }}
    </div>
</div>
</body>
</html>
