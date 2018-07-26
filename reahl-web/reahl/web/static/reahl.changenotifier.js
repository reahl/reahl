/* Copyright 2018 Reahl Software Services (Pty) Ltd. All rights reserved. */
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
    
    $.widget('reahl.changenotifier', {
        options: {
            name: undefined,
        },
        _create: function() {
                var o = this.options;
                var element = this.element;
                var _this = this;
    
                if (!o.name) { throw new Error("No name given in options. This is a required option.")}

                $(element).on( 'change', function(e) {
                    var newHashName = o.name;
                    var newHashValue = e.target.value;

                    var originalHash = window.location.hash;
                    var currentFragment = $.deparam.fragment(originalHash);
                    currentFragment[newHashName] = newHashValue;
                    var newHash = $.param.fragment(originalHash, currentFragment, 2);
                    window.location.hash = newHash;

                    $(window).hashchange();
                    return true;
                });
            },
    });
    
$.extend($.reahl.changenotifier, {
    version: '1.0'
});

})(jQuery);
    
    
    