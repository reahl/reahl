/* Copyright 2013-2018 Reahl Software Services (Pty) Ltd. All rights reserved. */
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

$.widget("reahl.textinput", {
    options: {
    },
    
    _create: function() {
        var o = this.options;
        this.element.addClass("reahl-textinput");

        var input = this.element;

        if ( input.hasClass('fuzzy') ) {
            input
                .on('blur', function(){
                    var data = {};
                    data[input.prop('name')] = input.prop('value');
                    var url = $(input[0].form).attr('data-formatter'); /*xxxxxx*/
                    $.ajax({
                        dataType: 'text',
                        url: url,
                        data: data,
                        success: function(data, textStatus, jqXHR) {
                            $(input).prop('value', data);
                        }
                    });
                });
        };
    }
});

$.extend($.reahl.textinput, {
    version: "1.8"
});

})(jQuery);


