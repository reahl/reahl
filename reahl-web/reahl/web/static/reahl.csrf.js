/* Copyright 2016-2022 Reahl Software Services (Pty) Ltd. All rights reserved. */
/*
    This file is part of Reahl.

    Reahl is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation; version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/


(function($) {
"use strict";
    // From: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html#use-of-custom-request-headers

    function isSameOrigin(urlString) {
      return new URL(document.baseURI).origin === new URL(urlString, document.baseURI).origin;
    }

    var originalOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(){
        var result = originalOpen.apply(this, arguments);
        if (isSameOrigin(arguments[1])) {
            var csrf_token = $('meta[name="csrf-token"]').attr('content');
            this.setRequestHeader("X-CSRF-TOKEN", csrf_token);
        }
        return result;
    };

    var originalFetch = window.fetch;
    window.fetch = function() {
        var argumentsArray = [].slice.call(arguments);
        var init = {};
        if (argumentsArray.length <= 1) {
            argumentsArray.push(init);
        } else {
            init = argumentsArray[1];
        }
        if (!('headers' in init)) {
            init.headers = new Headers();
        }
        if (isSameOrigin(arguments[0].toString())) {
            var csrf_token = $('meta[name="csrf-token"]').attr('content');
            init.headers.append("X-CSRF-TOKEN", csrf_token);
        }
        return originalFetch.apply(this, argumentsArray);
    }

})(jQuery);
