/* Copyright 2013-2022 Reahl Software Services (Pty) Ltd. All rights reserved. */
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

$.widget('reahl.form', {
    options: $.extend(true, {meta: 'validate'}, $.validator.defaults),

    _create: function() {
        var element = this.element;
        $(element).validate(this.options);
        
        var namespaced_submit = 'submit.'+element.attr('id');
        element.off(namespaced_submit).on(namespaced_submit, function(e) {
            if ($(element).valid()) {
                element.block({overlayCSS: {backgroundColor: '#fff', opacity: 0.3}, message: '', fadeIn: 0, fadeout: 0});
                $(element[0].elements)
                    .block({overlayCSS: {backgroundColor: '#fff', opacity: 0.3}, message: '', fadeIn: 0, fadeout: 0})
                    .attr('readonly', true);
            }
        });        

        element[0]
    }

});

$.extend($.reahl.form, {
    version: '1.8'
});

})(jQuery);


