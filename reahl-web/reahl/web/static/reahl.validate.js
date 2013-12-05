/* Copyright 2009, 2010, 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved. */
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


jQuery.validator.addMethod("pattern", function(value, element, params) {
    return this.optional(element) || value.match("^(?:"+params+")$"); 
    }, jQuery.validator.format("Does not match pattern.")); 



jQuery.validator.addMethod("data-equalTo2", function(value, element, param) {
    // bind to the blur event of the target in order to revalidate whenever the target field is updated
    // TODO find a way to bind the event just once, avoiding the unbind-rebind overhead
    var target = $(element).closest("form").find("input[name='"+param+"']");
    target.unbind(".validate-equalTo").bind("blur.validate-equalTo", function() {
        $(element).valid();
        });
    return value == target.val();

    }, jQuery.validator.format("Does not match.")); 


jQuery.validator.addMethod("data-filesize", function(value, element, param) {
    var maxSize = param;
    var withinLimits = true;
    var i = 0;
    for (i = 0; i < element.files.length; i += 1) {
    withinLimits = withinLimits && (element.files[i].size <= maxSize);
    }
    return withinLimits;
});


// Accept a value from a file input based on a required mimetype
jQuery.validator.addMethod("accept", function(value, element, param) {
    // Split mime on commas incase we have multiple types we can accept
    var typeParam = typeof param === "string" ? param.replace(/,/g, '|') : "image/*",
    optionalValue = this.optional(element),
    i, file;

    // Element is optional
    if(optionalValue) {
        return optionalValue;
    }

    if($(element).attr("type") === "file") {
        // If we are using a wildcard, make it regex friendly
        typeParam = typeParam.replace("*", ".*");

        // Check if the element has a FileList before checking each file
        if(element.files && element.files.length) {
            for(i = 0; i < element.files.length; i++) {
                file = element.files[i];

                // Grab the mimtype from the loaded file, verify it matches
                if(!file.type.match(new RegExp( ".?(" + typeParam + ")$", "i"))) {
                    return false;
                }
            }
        }
    }

    // Either return true because we've validated each file, or because the
    // browser does not support element.files and the FileList feature
    return true;
}, jQuery.format("Please enter a value with a valid mimetype."));


