<?php
// footer.php (Revised to ensure footer is not fixed and scrolls)
?>
            </div> </main> <footer class="app-footer">
            <div class="footer-content">
                &copy; OIC Audit Management System 2025
            </div>
        </footer>

        <div id="message"></div>
    </div> <script type="module">
        import { initializeApp } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-app.js";
        import { getAuth, signInAnonymously, signInWithCustomToken } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-auth.js";
        import { getFirestore, collection, getDocs, addDoc, doc, setDoc, deleteDoc } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-firestore.js";

        const firebaseConfig = JSON.parse(typeof __firebase_config !== 'undefined' ? __firebase_config : '{}');
        const appId = typeof __app_id !== 'undefined' ? __app_id : 'default-app-id';

        const app = initializeApp(firebaseConfig);
        const db = getFirestore(app);
        const auth = getAuth(app);

        // Sign in anonymously if no custom token is provided
        (async () => {
            try {
                if (typeof __initial_auth_token !== 'undefined' && __initial_auth_token) {
                    await signInWithCustomToken(auth, __initial_auth_token);
                    console.log("Signed in with custom token.");
                } else {
                    await signInAnonymously(auth);
                    console.log("Signed in anonymously.");
                }
            } catch (error) {
                console.error("Firebase authentication error:", error);
            }
        })();

        // Make db, auth, and appId globally accessible for operations_dosri.js
        window.db = db;
        window.auth = auth;
        window.appId = appId;
    </script>

    <script src="js/tabs/operations_aging_report.js"></script>
    <script src="js/tabs/operations_statement_of_account.js"></script>
    <script src="js/tabs/operations_deposit_counterpart.js"></script>
    <script src="js/tabs/operations_deposit_liabilities.js"></script>
    <script src="js/tabs/operations_dosri.js"></script>
    <script src="js/tabs/operations_form_emp.js"></script>
    <script src="js/tabs/gl_dos.js"></script>
    <script src="js/tabs/gl_win.js"></script>
    <script src="js/tabs/lnacc_dos.js"></script>
    <script src="js/tabs/lnacc_win.js"></script>
    <script src="js/tabs/svacc_dos.js"></script>
    <script src="js/tabs/svacc_win.js"></script>
    <script src="js/tabs/actg_gl.js"></script>
    <script src="js/tabs/actg_tb.js"></script>
    <script src="js/tabs/actg_ref.js"></script>
    <script src="js/tabs/actg_desc.js"></script>
    <script src="js/tabs/actg_trend.js"></script>
    <script src="js/tabs/actg_fs.js"></script>
    <script src="js/tabs/trnm_convert.js"></script>
    <script src="js/tabs/trnm_win.js"></script>
    <script src="js/tabs/trnm_combine.js"></script>
    <script src="js/tabs/aging_consolidated.js"></script>
    <script src="js/tabs/petty_cash.js"></script>
    <script src="js/tabs/bank_reconciliation.js"></script>
    <script src="js/tabs/journal_voucher.js"></script>
    <script src="js/tabs/login.js"></script>
    <script src="js/tabs/register.js"></script>
</body>
</html>