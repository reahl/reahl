/* Copyright 2016 Reahl Software Services (Pty) Ltd. All rights reserved. */
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

  $.widget('reahl.bootstrapform', {
    options: $.extend(true, {}, $.validator.defaults, {
      meta: 'validate',
      errorElement: 'span',
      errorClass: 'has-danger',
      validClass: 'has-success',
      onclick: function(element, event) {
        // click on selects, radiobuttons and checkboxes
        if ( element.name in this.submitted ) {
          this.element(element);
        }
        // or option elements, check parent select in that case
        else if (element.parentNode.name in this.submitted) {
          this.element(element.parentNode);
        }
      },
      highlight: function(element) {
        $(element).closest('.form-group').removeClass('has-success').addClass('has-danger');
      },
      unhighlight: function(element) {
        $(element).closest('.form-group').removeClass('has-danger').addClass('has-success');
      },
      errorPlacement: function (error, element) {
        error.addClass('text-help')
        element.closest('.form-group').append(error);
      }
    }),

    _create: function() {
      $(this.element).validate(this.options);
    }
  });

  $.extend($.reahl.bootstrapform, {
    version: '1.8'
  });

})(jQuery);


