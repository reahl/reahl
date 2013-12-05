/* Copyright 2010, 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved. */
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

$.widget('reahl.hashchange', {
    options: {
        hashChangeHandlers: [{
            url: '',
            cache: true,
            errorMessage: 'Ajax error',
            timeoutMessage: 'Ajax timeout',
            params: []
        }]
    },

    _create: function() {
        var o = this.options;
        var element = this.element;

        for (var x in o.hashChangeHandlers) {
            var hashChangeHandler = o.hashChangeHandlers[x];
            $(window).bind( 'hashchange', function(e) {
                var currentHashValues = e.getState();
                var changed = false;
                var changedParams = $.extend(true, {}, hashChangeHandler.params);

                for (var name in changedParams) {
                    if (currentHashValues[name] && currentHashValues[name] != changedParams[name]) {
                        changed = true;
                        changedParams[name] = currentHashValues[name];
                    }
                }
                if (changed) {
                    var loading = element.block({message: ''});
                    $.ajax({url:     hashChangeHandler.url,
                            cache:   hashChangeHandler.cache,
                            data:    changedParams,
                            success: function(data){
                                element.fadeOut('fast', function(){element.html(data).fadeIn();});
                                hashChangeHandler.params = changedParams;
                            },
                            complete: function(data){
                                element.unblock();
                            }
                    });
                };
                return true;
            });
        }

        $(window).trigger( 'hashchange' );
    }
});

$.extend($.reahl.hashchange, {
    version: '1.8'
});

})(jQuery);


