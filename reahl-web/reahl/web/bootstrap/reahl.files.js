/* Copyright 2016, 2018 Reahl Software Services (Pty) Ltd. All rights reserved. */
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

  $.widget('reahl.bootstrapfileinput', {
      options: {
	  nfilesMessage: 'files',
	  nofilesMessage: 'No file chosen'
      },
      _create: function() {
	  var this_ = this;
	  $(this.element).find("input[type='file']").on('change', function(e) {

	      var fileName = '';

	      if( this.files && this.files.length > 1 )
		  fileName = ( this.files.length + ' ' + this_.options.nfilesMessage );
	      else if( this.value )
		  fileName = this.value.split( '\\' ).pop();
	      else
		  fileName = this_.options.nofilesMessage;

	      $(this_.element).find('span[class="form-control"]').html( fileName );
	  })
      }
  });

  $.extend($.reahl.bootstrapfileinput, {
      version: '4'
  });

})(jQuery);


(function($) {
"use strict";

  $.widget('reahl.bootstrapfileinputbutton', {
      options: {
      },
      _create: function() {
	  var this_ = this;
	  var $fileInput = $(this.element).find("input[type='file']");
	  $fileInput
	      .on('focus', function(){
		  $(this_.element).addClass('focus'); 
	      })
	      .on('blur', function(){
		  $(this_.element).removeClass('focus'); 
	      });
      }
  });

  $.extend($.reahl.bootstrapfileinputbutton, {
      version: '4'
  });

})(jQuery);


