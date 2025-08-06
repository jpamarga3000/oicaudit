<?php
// pages/admin_profile.php
// This file contains the HTML structure for the Admin Profile section.
// It will display and allow editing of user information from the PHP session.
?>
<div id="adminProfile" class="vertical-tab-pane">

        <div class="bg-white p-6 rounded-lg shadow-md flex flex-col md:flex-row gap-8">
            <div class="flex-shrink-0 flex flex-col items-center md:w-1/3 p-4 border-r md:border-r-0 md:border-b-0 border-gray-200">
                <div class="profile-pic-container w-full bg-gray-200 flex items-center justify-center overflow-hidden mb-4 rounded-lg">
                    <img id="profilePic" src="https://placehold.co/160x160/cbd5e1/475569?text=Profile" alt="Profile Picture" class="w-full h-full object-cover">
                </div>
                <input type="file" id="uploadProfilePic" class="hidden" accept="image/*">
                <label for="uploadProfilePic" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg cursor-pointer transition duration-150 ease-in-out">
                    Upload Photo
                </label>
            </div>

            <div class="flex-grow p-4">
                <h3 class="text-2xl font-semibold text-gray-700 mb-4 border-b pb-2">Account Information</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <div>
                        <label for="profileFirstName" class="block text-gray-700 text-sm font-bold mb-2">First Name:</label>
                        <input type="text" id="profileFirstName" class="shadow appearance-none border rounded-lg w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline" readonly value="<?php echo htmlspecialchars($_SESSION['first_name'] ?? ''); ?>">
                    </div>
                    <div>
                        <label for="profileLastName" class="block text-gray-700 text-sm font-bold mb-2">Last Name:</label>
                        <input type="text" id="profileLastName" class="shadow appearance-none border rounded-lg w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline" readonly value="<?php echo htmlspecialchars($_SESSION['last_name'] ?? ''); ?>">
                    </div>
                    <div>
                        <label for="profileContactNumber" class="block text-gray-700 text-sm font-bold mb-2">Contact Number:</label>
                        <input type="text" id="profileContactNumber" class="shadow appearance-none border rounded-lg w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline" readonly value="<?php echo htmlspecialchars($_SESSION['contact_number'] ?? ''); ?>">
                    </div>
                    <div>
                        <label for="profileBirthdate" class="block text-gray-700 text-sm font-bold mb-2">Birthdate:</label>
                        <input type="text" id="profileBirthdate" class="shadow appearance-none border rounded-lg w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline" readonly value="<?php echo htmlspecialchars($_SESSION['birthdate'] ?? ''); ?>">
                    </div>
                    <div>
                        <label for="profileEmail" class="block text-gray-700 text-sm font-bold mb-2">Email:</label>
                        <input type="email" id="profileEmail" class="shadow appearance-none border rounded-lg w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline" readonly value="<?php echo htmlspecialchars($_SESSION['email'] ?? ''); ?>">
                    </div>
                    <div>
                        <label for="profileUsername" class="block text-gray-700 text-sm font-bold mb-2">Username:</label>
                        <input type="text" id="profileUsername" class="shadow appearance-none border rounded-lg w-full py-2 px-3 text-gray-700 bg-gray-100 leading-tight focus:outline-none focus:shadow-outline" readonly value="<?php echo htmlspecialchars($_SESSION['username'] ?? ''); ?>">
                    </div>
                    <div>
                        <label for="profileBranch" class="block text-gray-700 text-sm font-bold mb-2">Branch:</label>
                        <!-- Branch field is now always readonly and disabled -->
                        <input type="text" id="profileBranch" class="shadow appearance-none border rounded-lg w-full py-2 px-3 text-gray-700 bg-gray-100 leading-tight focus:outline-none focus:shadow-outline" readonly disabled value="<?php echo htmlspecialchars($_SESSION['branch'] ?? ''); ?>">
                    </div>
                </div>
                <div class="mt-8 flex justify-end space-x-4">
                    <button id="editProfileButton" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg focus:outline-none focus:shadow-outline transition duration-150 ease-in-out">
                        Edit Profile
                    </button>
                    <button id="saveProfileButton" class="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg focus:outline-none focus:shadow-outline transition duration-150 ease-in-out hidden">
                        Save Changes
                    </button>
                    <button id="cancelEditButton" class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded-lg focus:outline-none focus:shadow-outline transition duration-150 ease-in-out hidden">
                        Cancel
                    </button>
                </div>

                <!-- New section for Biometrics -->
                <div class="mt-8 border-t pt-6">
                    <h3 class="text-2xl font-semibold text-gray-700 mb-4 border-b pb-2">Biometric Authentication</h3>
                    <div class="flex items-center justify-between mb-4">
                        <span class="text-gray-700">Biometric Status: <span id="biometricStatus" class="font-semibold text-red-500">Not Enrolled</span></span>
                        <button id="enrollBiometricsButton" class="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded-lg focus:outline-none focus:shadow-outline transition duration-150 ease-in-out">
                            Enroll Biometrics
                        </button>
                    </div>
                    <p class="text-sm text-gray-600">
                        Enroll Face ID or Fingerprint for faster and more secure login.
                        This feature depends on your device's capabilities.
                    </p>
                </div>
                <!-- End New section for Biometrics -->

                <div id="profileMessage" class="hidden p-3 rounded-md mt-4 text-center"></div>
            </div>
        </div>
    </div>
    <script src="js/tabs/admin_profile.js"></script>
</div>
