/* Copyright 2013 Reahl Software Services (Pty) Ltd. All rights reserved. */
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



;(function($) {
"use strict";

  $.widget('reahl.slidingpanel', {
      _create: function() {
          var _this = this;
          $(this.element).find(">a").first().click(function(){
              _this.slide(-1);
              return false;
          });
          $(this.element).find(">a").last().click(function(){
              _this.slide(+1);
              return false;
          });
          this.timer = false;
          this.setTimer();
      },
      setTimer: function() {
          var _this = this;
          if (this.timer) { clearInterval(this.timer); }
          this.timer = setInterval(function(){ _this.slide(+1); }, 15000);
      },
      getCurrent: function() {
          return $(this.element).find("div.contained:visible")[0];
      },
      getNext: function(current, offset) {
          var contained = $(this.element).find("div.contained");
          var currentIndex = contained.index(current)+1;
          var wrappedArray = [contained.last()[0]].concat(contained.toArray(), [contained.first()[0]]);
          return wrappedArray[currentIndex+offset];
      },
      slide: function(offset) {
          var currentDirection = offset > 0 ? 'left': 'right';
          var nextDirection = offset > 0 ? 'right': 'left';
          var current = this.getCurrent();
          $(current).toggle('slide', {direction: currentDirection}, 'slow');
          $(this.getNext(current, offset)).toggle('slide', {direction: nextDirection}, 'slow');
          this.setTimer();
      }
  });
 
    
  $.extend($.reahl.slidingpanel, {
      version: '1.8'
  });

})(jQuery);


