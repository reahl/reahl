/* Copyright 2013-2020 Reahl Software Services (Pty) Ltd. All rights reserved. */
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

$.widget('reahl.bootstrapfileuploadpanel', {
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
        return $(this.element).find('input[name^="event.'+this.getFormId()+'-upload_file"]');
    },
    getRemoveFileButtonName: function() {
        return 'event.'+this.getFormId()+'-remove_file';
    },
    getFileInput: function() {
        return $(this.element).find('input[type="file"]');
    },
    getValidationError: function() {
        return $(this.element).find('span[for="'+this.fileInputName+'"][class~="invalid-feedback"]');
    },
    getNumberOfUploadedFiles: function() {
        return $(this.element).find('li').length;
    },
    _create: function() {
        var this_ = this;

        this.queuedUploads = [];
        this.uploadInputName = this.getUploadInput().attr('name');
        this.fileInputName = this.getFileInput().attr('name');
        this.duplicateValidationError = $('<span data-generated-for="'+this.fileInputName+'" class="invalid-feedback">'+this.options.duplicateValidationErrorMessage+'</span>');
        this.uploadCounter = 0;

        $(this.element).on('click', 'input[name="'+this_.uploadInputName+'"]', function(e){
            var clickedInput = this;
            if ($('#'+this_.getFormId()).validate().form() ) {
                var files = this_.getFileInput()[0].files;
                for (var fileIdx=0; fileIdx<files.length; fileIdx+=1) {
                    var fileUpload = this_.createFileUpload(files[fileIdx]);
                    fileUpload.startUpload(clickedInput.name, this_.options);
                    this_.clearFileInput();  
                }
            }
            e.preventDefault();
        });
        
        $(this.element).on('click', 'input[name^="'+this.getRemoveFileButtonName()+'"]', function(e) {
            var clickedInput = this;
            var fileUpload = $(clickedInput).closest('li').data('reahl-bootstrapfileuploadli');
            fileUpload.removeUploaded();
            e.preventDefault();
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
            this_.getUploadInput().trigger("click");
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
    createFileUpload: function(file) {
        var uploadLi = $('<li></li>').bootstrapfileuploadli({file: file, fileInputPanel: this}).data('reahl-bootstrapfileuploadli');
        $(this.element).find('ul').append(uploadLi.element);
        return uploadLi;
    },
    processUploadQueue: function() {
        var upload = this.queuedUploads.shift();
        if (upload) {
            upload.start();
        }
    },
    uploadStarted: function(filename, startFunction) {
        this.queuedUploads.push({name:filename, start:startFunction});
        if (this.uploadCounter === 0) {
            this.processUploadQueue();
        }
        this.uploadCounter += 1;
    },
    cancelQueuedUpload: function(filename) {
        var newUploadQueue = [];
        for (var i=0; i<this.queuedUploads.length; i+=1) {
            var upload = this.queuedUploads[i];
            if (upload.name != filename) {
                newUploadQueue.push(upload);
            }
        };
        this.queuedUploads = newUploadQueue;
        this.uploadCounter -= 1;
    },
    cancelCurrentlyUploading: function() {
        this.uploadFinished();
    },
    uploadFinished: function() {
        this.uploadCounter -= 1;
        this.processUploadQueue();
    },
    clearFileInput: function() {
        this.getFileInput().val('').trigger('change');
    }
});



$.extend($.reahl.bootstrapfileuploadpanel, {
    version: '1.8'
});


jQuery.validator.addMethod("maxfiles", function(value, element, param) {
    var maxFiles = param;
    var startedUploads = 0;
    var fileUploadPanel = $(element).closest('.reahl-bootstrap-file-upload-panel').data('reahl-bootstrapfileuploadpanel');
    if (fileUploadPanel) {
	startedUploads = fileUploadPanel.getNumberOfUploadedFiles();
    }
    return startedUploads + element.files.length <= maxFiles;
});

jQuery.validator.addMethod("uniquefiles", function(value, element, param) {
    var fileUploadPanel = $(element).closest('.reahl-bootstrap-file-upload-panel').data('reahl-bootstrapfileuploadpanel');

    var files = fileUploadPanel.getFileInput()[0].files;
    for (var fileIdx=0; fileIdx<files.length; fileIdx+=1) {
        if (fileUploadPanel.isAlreadyUploaded(files[fileIdx].name)) {
            return false;
        }
    }
    return true;
});


})(jQuery);



