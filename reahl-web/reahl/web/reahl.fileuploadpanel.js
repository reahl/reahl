/* Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved. */
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

$.widget('reahl.fileuploadpanel', {
    options: {
        form_id: '',
        nested_form_id: '',
        input_form_id: '',
        duplicateValidationErrorMessage: 'no duplicates allowed',
        waitForUploadsMessage: 'please wait, uploads in progress',
        errorMessage: 'Ajax error',
        removeLabel: 'Remove',
        cancelLabel: 'Cancel'
    },

    getFormId: function() {
        return this.options.form_id;
    },
    getNestedFormId: function() {
        return this.options.nested_form_id;
    },
    getInputFormId: function() {
        return this.options.input_form_id;
    },
    getRemoveLabel: function() {
        return this.options.removeLabel;
    },

    getCancelLabel: function() {
        return this.options.cancelLabel;
    },

    getErrorMessage: function() {
        return this.options.errorMessage;
    },
    getUploadInput: function() {
        return $(this.element).find('input[name^="event.upload_file"]');
    },
    getFileInput: function() {
        return $(this.element).find('input[type="file"]');
    },
    getValidationError: function() {
        return $(this.element).find('label[for="'+this.fileInputName+'"][class~="error"]');
    },
    getNumberOfUploadedFiles: function() {
        return $(this.element).find('li').length;
    },
    _create: function() {
        var this_ = this;

        this.queuedUploads = [];
        this.uploadInputName = this.getUploadInput().attr('name');
        this.fileInputName = this.getFileInput().attr('name');
        this.duplicateValidationError = $('<label for="'+this.fileInputName+'" class="error">'+this.options.duplicateValidationErrorMessage+'</label>')
        this.uploadCounter = 0;

        $(this.element).on('click', 'input[name="'+this_.uploadInputName+'"]', function(e){
            var clickedInput = this;
            this_.clearValidationError();
            if ($('#'+this_.getFormId()).valid() ) {
                var files = this_.getFileInput()[0].files;
                for (var fileIdx=0; fileIdx<files.length; fileIdx+=1) {
                    var fileUpload = this_.createFileUpload(files[fileIdx]);
                    fileUpload.startUpload(clickedInput.name, this_.options);
                };
            };
            return false;
        });
        
        $(this.element).on('click', 'input[name^="event.remove_file"]', function(e) {
            var clickedInput = this;
            var fileUpload = $(clickedInput).closest('li').data('reahl-fileuploadli');
            fileUpload.removeUploaded();
            return false;
        });

/* This is necessary iff multiple="multiple" on an input with type="file". If that's on,
   it will keep adding more files to the list, including the previous ones that may
   already be uploaded. I suspect we should NOT enable multiple=multiple for this widget,
   since our testing infrastructure cannot handle it.
*/
        $(this.element).on('click', 'input[type="file"]', function(){
            $('#'+this_.getFormId()).clearForm();
        });
        $(this.element).on('change', 'input[type="file"]', function(){
            this_.getUploadInput().click();
        });
        $('#'+this.getInputFormId()).on('submit', function() {
            if (this_.uploadCounter > 0) {
                alert(this_.options.waitForUploadsMessage);
                return false;
            } else {
                return true;
            }
        });
    },
    isAlreadyUploaded: function(filename) {
        var filenames = $(this.element).find('li').find('span').filter(function() {
            return $(this).text() === filename;
        });
        return filenames.length > 0;
    },
    showValidationError: function(filename) {
        this.getFileInput().after(this.duplicateValidationError);
        this.getFileInput().addClass('error');
    },
    clearValidationError: function(filename) {
        this.getValidationError().remove();
        this.getFileInput().removeClass('error');
    },
    createFileUpload: function(file) {
        var uploadLi = $('<li></li>').fileuploadli({file: file, fileInputPanel: this}).data('reahl-fileuploadli');
        $(this.element).find('ul').append(uploadLi.element);
        return uploadLi;
    },
    processUploadQueue: function() {
        var startUpload = this.queuedUploads.shift();
        if (startUpload) {
            startUpload();
        }
    },
    uploadStarted: function(startFunction) {
        this.queuedUploads.push(startFunction);
        if (this.uploadCounter === 0) {
            this.processUploadQueue();
        }
        this.uploadCounter += 1;
    },
    uploadFinished: function() {
        this.uploadCounter -= 1;
        this.processUploadQueue();
    },
    clearFileInput: function() {
        this.getFileInput()[0].value = '';
    }
});



$.extend($.reahl.fileuploadpanel, {
    version: '1.8'
});


jQuery.validator.addMethod("data-maxfiles", function(value, element, param) {
    var maxFiles = param;
    if (element.files.length > maxFiles) {
        return false
    };

    var fileUploadPanel = $(element).closest('.reahl-file-upload-panel').data('reahl-fileuploadpanel');
    if (fileUploadPanel) {
        return fileUploadPanel.getNumberOfUploadedFiles() + 1 <= maxFiles;
    };
    
    return true;
});

jQuery.validator.addMethod("data-uniquefiles", function(value, element, param) {
    var fileUploadPanel = $(element).closest('.reahl-file-upload-panel').data('reahl-fileuploadpanel');

    var files = fileUploadPanel.getFileInput()[0].files;
    for (var fileIdx=0; fileIdx<files.length; fileIdx+=1) {
        if (fileUploadPanel.isAlreadyUploaded(files[fileIdx].name)) {
            return false;
        };
    };
    return true;
});


})(jQuery);



