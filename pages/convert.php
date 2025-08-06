<?php
// pages/convert.php (Modified: Changed button text, added download button placeholder)
?>
<div id="convert" class="tab-content hidden">
    <div class="p-4">
        <h2 class="text-2xl font-bold mb-4">TRNM DOS DBF to CSV Conversion</h2>
        <p class="text-gray-700 mb-6">
            Convert DBF files from TRNM DOS into CSV format. The converted files will be stored temporarily and can then be downloaded.
        </p>

        <div class="bg-white p-6 rounded-lg shadow-md mb-6">
            <h3 class="text-xl font-semibold mb-4">Upload DBF Files</h3>
            <form id="convertDbfForm" enctype="multipart/form-data">
                <div class="mb-4">
                    <label for="dbfFiles" class="block text-gray-700 text-sm font-bold mb-2">Select DBF Files:</label>
                    <input type="file" id="dbfFiles" name="files[]" multiple accept=".dbf"
                           class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline">
                </div>

                <div class="mb-4">
                    <label class="block text-gray-700 text-sm font-bold mb-2">Selected Files:</label>
                    <div id="convertDbfFilesDisplay" class="mt-2 p-3 border border-gray-300 rounded min-h-[50px] text-gray-500">
                        No files selected.
                    </div>
                </div>

                <button type="submit" id="convertButton" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline">
                    Convert
                </button>
            </form>
            
            <!-- Download Button Placeholder -->
            <div id="downloadSection" class="mt-6 hidden">
                <p class="text-gray-700 mb-4">Conversion complete. Click below to download your files.</p>
                <button id="downloadConvertedFilesButton" class="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline">
                    Download Converted Files
                </button>
            </div>
        </div>
    </div>

    <!-- Loading Animation Container -->
    <div id="loadingOverlay" class="fixed inset-0 bg-gray-800 bg-opacity-75 flex flex-col items-center justify-center z-50 hidden">
        <div class="relative">
            <img src="images/logo.png" alt="Loading" id="loadingLogo" class="w-24 h-24 mb-4">
            <div class="loading-text text-white text-lg font-semibold">Processing...</div>
        </div>
    </div>
</div>

<script src="js/tabs/trnm_convert.js" defer></script>
