"use strict";
var page = require('webpage').create(), system = require('system'), address, output;

if (system.args.length < 3) {
    phantom.exit(1);
} else {
    address = system.args[1];
    output = system.args[2];
    page.viewportSize = {width: 480, height: 640};
    page.paperSize = {format: 'A4', orientation: 'portrait', margin: '1cm'};

    page.open(address, function (status) {
        if (status !== 'success') {
            console.log('Unable to load the address!');
            phantom.exit(1);
        } else {
            window.setTimeout(function () {
                page.render(output);
                phantom.exit();
            }, 175);
        }
    });
}
