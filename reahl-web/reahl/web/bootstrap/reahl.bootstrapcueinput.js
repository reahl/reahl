/* Copyright 2013-2023 Reahl Software Services (Pty) Ltd. All rights reserved. */
/*
    This file is part of Reahl.

    Reahl is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as
    published by the Free Software Foundation; version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/


(function($) {
"use strict";

$.widget("reahl.bootstrapcueinput", {
	_create: function() {
	    var o = this.options;
	    this.element.addClass("reahl-bootstrapcueinput");

		var input = this.element.find('input');
	    var cue = this.element.find('.reahl-bootstrapcue');

        cue.attr('hidden', 'true');

        input
            .on('focus', function(ev){
                cue.removeAttr('hidden');
            })
            .on('blur', function(ev){
                cue.attr('hidden', 'true');
			}); 
	}
});

$.extend($.reahl.bootstrapcueinput, {
	version: "1.0"
});

})(jQuery);


