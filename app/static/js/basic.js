$(document).ready(function() {

    $('#signOutBtn').click(function(event) {
        event.preventDefault(); // 기본 링크 동작 방지
        SignOut();
    });

    $('#myProfileBtn').click(function(event) {
        $('#ProfileModal').modal('show');
    });

    $('body').on('click', '#saveProfileBtn', function(event) {
        event.preventDefault();
        const FFsession = getSessionFromMemory();
        const userId = $('#profileId').val();
        const userData = {
          ID: $('#profile_ID').val(), 
          name: $('#profile_name').val(), 
          hire_date: $('#profile_hire_date').val(), 
          role: $('#profile_role').val(),
        };

        $.ajax({
            url: `/updateUser/${userId}`,
            type: 'PUT',
            headers: {
                'Authorization': 'Bearer ' + FFsession['session_token']
              },
            contentType: 'application/json',
            data: JSON.stringify(userData),
            success: function(response) {
                if (response.status === 'success') {
                    alert('Company updated successfully!');
                    window.location.reload();
                } else {
                    alert('Error updating company: ' + response.message);
                }
            },
            error: function(xhr, status, error) {
                alert('An error occurred: ' + error);
            }
        });
    });

});

function SignOut(){

    $.ajax({
        url: '/signout', // 로그아웃 요청 URL
        type: 'POST', // POST 메서드 사용
        success: function(response) {
            if (response.status === 'success') {
                localStorage.removeItem('portfolio_user_id');
                localStorage.removeItem('portfolio_user_id_expiration');
                alert('Logged out successfully!');
                window.location.href = '/signin'; 
            } else {
                alert('Error logging out: ' + response.message); 
                window.location.href = '/signin';
            }
        },
        error: function(xhr, status, error) {
            alert('An error occurred: ' + error);
        }
    });
}

function profileDataMapping(info) {
    console.log(info);
    $('#profileId').val(info._id); 
    $('#profile_ID').val(info.ID); 
    $('#profile_name').val(info.name); // 사용자 이름
    $('#profile_hire_date').val(info.hire_date); // 고용 날짜
    $('#profile_role').val(info.role); // 역할
    // profile 
    $('#profileName1').text(info.name); 
    $('#profileName2').text(info.name); 
    $('#profileRole').text(info.role);
    $('#profilecreatedAt').text(info.createdAt.substring(0, 10));  

}

function getSessionFromMemory() {
    const JSON_session = localStorage.getItem('fileflicker_session');
    if (!JSON_session) {
        window.location.href = '/signin';
        return;
    }
    const session = JSON.parse(JSON_session);

    userId = session['user_id'];
    sessionToken = session['session_token'];
    created_at = session['created_at'];

    if (!userId || !sessionToken || !created_at) {
        localStorage.setItem('fileflicker_session', '');
        window.location.href = '/signin';
    }

    const createdAtDate = new Date(created_at);
    const currentTime = new Date();

    const LimitHour = 1; // Hour (서버에서도 바꿔야 함)
    const LimitTime = LimitHour * 60 * 60 * 1000; // 밀리초로 변환

    if ((currentTime.getTime() - createdAtDate.getTime()) > LimitTime) {
        localStorage.setItem('fileflicker_session', '');
        window.location.href = '/signin';
        return; 
    }

    return session; 
}

function ProfileModal() {
    const modalHtml = `
        <div class="modal fade" tabindex="-1" id="ProfileModal" role="dialog" aria-labelledby="ProfileModalLabel">
            <div class="modal-dialog" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
                        <h4 class="modal-title" id="addUserBtn">Update My Profile</h4>
                    </div>
                    <div class="modal-body">
                        <form id="UserForm">
                            <div class="form-group">
                                <label for="profile_ID">User ID</label>
                                <input type="text" class="form-control" id="profile_ID" placeholder="Enter user ID" readonly>
                            </div>
                            <div class="form-group">
                                <label for="profile_name">Name</label>
                                <input type="text" class="form-control" id="profile_name" placeholder="Enter name" required>
                            </div>
                            <div class="form-group">
                                <label for="profile_hire_date">Hire Date</label>
                                <input type="date" class="form-control" id="profile_hire_date" required>
                            </div>
                            <div class="form-group">
                                <label for="profile_role">Role</label>
                                <input type="text" class="form-control" id="profile_role" readonly>
                            </div>
                            <input type="hidden" id="profileId" value="">
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
                        <button type="button" class="btn btn-primary" id="saveProfileBtn">Save</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    $('body').append(modalHtml);
};

async function downloadFile(fileId, fileName, mode) {
    try {
        const response = await fetch(`/downloadFile/${fileId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            let errorMessage = 'An error occurred';
            const contentType = response.headers.get('Content-Type');
            if (contentType && contentType.includes('application/json')) {
                const errorData = await response.json();
                errorMessage = errorData.error || errorMessage;
            }
            alert(`Error: ${errorMessage}`);
            return;
        }

        const blob = await response.blob(); 
        let temp_data = await blob.text(); 
        const textData = JSON.parse(temp_data);

        if (mode == 'pass') {
            return textData; 
        } else if (mode == 'download') {
            if (!textData.url) {
                alert('유효하지 않은 다운로드 URL입니다.');
                return;
            }
            const a = document.createElement('a');
            a.href = textData.url;
            a.download = fileName; 
            document.body.appendChild(a);
            a.click(); 
            a.remove(); 
            window.URL.revokeObjectURL(textData.url);
        } else {
            alert('Mode should be needed.');
        }

    } catch (error) {
        alert(`Error: ${error.message}`);
        throw error;
    }
}

async function downloadFileFromS3(s3_key) {
    try {
        const url = `https://s3.us-west-1.amazonaws.com/${s3_key}`;
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error('파일 다운로드 실패');
        }
        return await response.blob(); // Blob 형태로 반환
    } catch (error) {
        console.error('S3에서 파일 다운로드 중 오류 발생:', error);
        throw error; // 오류를 다시 던져서 호출한 곳에서 처리할 수 있도록 함
    }
}

async function registMissingFilesInAWS() {
    try {
        const response = await fetch('/registMissingFilesInAWS', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        const data = await response.json();
        if (data.status === 'success') {
            alert('파일이 성공적으로 가져와졌습니다.');
            // 추가적인 처리 (예: 파일 목록 갱신)
        } else {
            alert('파일 가져오기 실패: ' + data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('서버 호출 중 오류가 발생했습니다.');
    }
}

async function getUser(userId, sessionToken) {
    try {
        const response = await $.ajax({
            url: `/users/getUser/${userId}`,
            method: 'GET',
            headers: {
                'Authorization': 'Bearer ' + sessionToken
            },
        });

        if (response.status === 'success') {
            return {'status': 'success', 'data': response.data};
        } else {
            // 응답이 성공적이지 않은 경우
            return {'status': 'error', 'message': response.message || 'Failed to retrieve user data.'};
        }
    } catch (error) {
        // AJAX 요청이 실패한 경우
        return {'status': 'error', 'message': error.statusText || 'An error occurred while fetching user data.'};
    }
}

function splitIntoChunks(text, maxLength) {
    const chunks = [];
    let sentences = text.match(/[^.!?]+[.!?]+/g) || [text];
    
    let currentChunk = '';
    for (const sentence of sentences) {
        if ((currentChunk + sentence).length <= maxLength) {
            currentChunk += sentence;
        } else {
            if (currentChunk) {
                chunks.push(currentChunk.trim());
            }
            currentChunk = sentence;
        }
    }
    
    if (currentChunk) {
        chunks.push(currentChunk.trim());
    }
    
    return chunks;
}

const truncateText = (text, maxLength) => text.length <= maxLength ? text : text.slice(0, maxLength - 3) + '...';
