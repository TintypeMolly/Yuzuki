var submit_lock = false;
var chat_input = $("#chat-input");
var message_ul = $("#chat-message-ul");
var latest_uid = 1;

var KEY_CODES = {
    UP_ARROW: 38,
    DOWN_ARROW: 40
};

var chat_histories = {
    init: function (params) {
        params = params || {};
        this.max_size = params["max_size"] || 20;
        this.histories = [];
        this.cursor_index = -1;
        return this;
    },
    size: function () {
        return this.histories.length;
    },
    add: function (history) {
        this.histories.unshift(history);
        if (this.histories.length > this.max_size) {
            this.histories.pop();
        }
    },
    next: function () {
        this.cursor_index = (this.cursor_index + 1) % this.size();
        return this.histories[this.cursor_index];
    },
    prev: function () {
        if (this.cursor_index === -1) {
            this.cursor_index = 0;
        }
        this.cursor_index = (this.cursor_index + this.size() - 1) % this.size();
        return this.histories[this.cursor_index];
    },
    reset: function () {
        this.cursor_index = -1;
    }
};

var chat_input_box = {
    init: function (params) {
        this.chat_input = $("#chat-input");
        this.chat_histories = chat_histories.init();

        var mentionable_users = params["mentionable_users"] || [];
        mentionable_users.unshift("전체");

        this.chat_input.textcomplete([
            {
                match: /\B@([-_a-zA-Z가-힣\d\(\)]*)$/,
                search: function (term, callback) {
                    callback($.map(mentionable_users, function (user) {
                        return user.indexOf(term) === 0 ? user : null;
                    }));
                },
                replace: function (value) {
                    return "@" + value + " ";
                },
                index: 1
            }
        ]);

        this.chat_input.on("keydown", $.proxy(this.on_keydown, this));
    },
    on_keydown: function (e) {
        if (e.keyCode === KEY_CODES["UP_ARROW"]) {
            this.set_text(this.chat_histories.next());
        }
        else if (e.keyCode === KEY_CODES["DOWN_ARROW"]) {
            this.set_text(this.chat_histories.prev());
        }
    },
    display_chat_input: function (show) {
        var chat_input_with_submit = this.chat_input.parent();
        if (show) {
            chat_input_with_submit.show()
        } else {
            chat_input_with_submit.hide();
        }
    },
    get_text: function () {
        return this.chat_input.val();
    },
    set_text: function (text) {
        this.chat_input.val(text)
    },
    finalize: function () {
        this.chat_histories.add(this.get_text());
        this.chat_histories.reset();
        this.set_text("");
    }
};

var chat_pagination = {
    init: function (params) {
        this.page_total = params["page_total"] || 1;
        this.current_page = params["current_page"] || 1;
        this.max_visible = params["max_visible"] || 10;
        this.leaps = params["leaps"] || false;
        this.chat_pagination = $("#pagination");

        this.chat_pagination.bootpag({
            total: this.page_total,
            page: this.current_page,
            maxVisible: this.max_visible,
            leaps: this.leaps,
            renderNew: true
        }).on({
            page: $.proxy(this.load_chat_items, this)
        });

        this.chat_pagination.trigger("page", this.current_page);
    },
    load_chat_items: function (e, page) {
        $.ajax("/chat/message/data", {
            data: {page: page},
            dataType: "json"
        }).done(function (data) {
            this.change_page(page);
            process_chat_items(data);
        }.bind(this));
    },
    change_page: function (page) {
        this.current_page = page;
        chat_input_box.display_chat_input(page === 1);
    }
};

$("#chat-form").submit(function (e) {
    if (!submit_lock) {
        submit_lock = true;
        $.post("/chat/message/stream", $(this).serialize()).done(function () {
            chat_input_box.finalize();
            submit_lock = false;
        }).fail(function (xhr) {
            var template = '<li class="chat-item row" class="chat-system"><div class="chat-item-user-nickname col-xs-2">system</div><div class="chat-content-datetime col-xs-10"><span class="chat-content">{{content}}</span><span class="chat-datetime">{{created_at}}</div></li>';
            var now = new Date();
            var year = now.getFullYear() % 1000;
            var month = now.getMonth();
            month += 1;
            month = month < 10 ? "0" + month : month;
            var date = now.getDate();
            date = date < 10 ? "0" + date : date;
            var hour = now.getHours();
            hour = hour < 10 ? "0" + hour : hour;
            var minute = now.getMinutes();
            minute = minute < 10 ? "0" + minute : minute;
            var second = now.getSeconds();
            second = second < 10 ? "0" + second : second;
            var created_at = year + "-" + month + "-" + date + " " + hour + ":" + minute + ":" + second;
            var system_message = {
                content: xhr.responseText,
                created_at: created_at
            };
            var rendered = Mark.up(template, system_message);
            message_ul.append(rendered);
            chat_input.val("");
            submit_lock = false;
        });
    }
    return false;
});

var process_chat_items = function (data, enable_noti) {
    for (var i = 0; i < data.length; i++) {
        (function () {
            latest_uid = Math.max(latest_uid, data[i].uid);
            var chat_item = data[i];
            var template =
                '<li class="chat-item row" style="color: #{{ user_chat_color }};" id="chat-{{ uid }}">' +
                '<div class="chat-item-user-nickname col-xs-2">' +
                '<a onclick="open_user_popup({{ user_id }})">{{ user_nickname }}</a>' +
                '</div>' +
                '<div class="chat-content-datetime col-xs-10">' +
                '<span class="chat-content">{{ content }}</span>' +
                '<span class="chat-datetime">{{ created_at }}</span>' +
                '</div>' +
                '</li>';
            var rendered = $(Mark.up(template, chat_item));


            var contain_noti = chat_item.content.split(" ").some(function (content) {
                return content === "@" + user_nickname || content === "@전체";
            });
            if (contain_noti) {
                rendered.addClass("chat-noti");
                var strip_content = $(document.createElement("div")).html(chat_item.content).text();
                var options = {
                    body: strip_content,
                    icon: "/favicon.ico"
                };
                if (enable_noti === true &&
                    Notification.permission === "granted" &&
                    chat_item.user_nickname !== user_nickname) {
                    var notification = new Notification(chat_item.user_nickname, options);
                    notification.onclick = function () {
                        window.focus();
                        var chat_selector = "#chat-" + chat_item.uid;
                        $(chat_selector).effect("highlight", 1500);
                    };
                }
            }

            message_ul.append(rendered);
            if (message_ul.children().length > chat_per_page) {
                message_ul.children().first().remove();
            }
        })();
    }
};

var get_newer_chat = function (enable_noti) {
    if (chat_pagination.current_page != 1) {
        return;
    }

    return $.ajax("/chat/message/data?id=" + latest_uid, {
        dataType: "json"
    }).done(function (data) {
        process_chat_items(data, enable_noti);
    });
};

var wait_for_chat_stream = function () {
    $.ajax("/chat/message/stream", {
        cache: false
    }).done(function () {
        get_newer_chat(true);
        wait_for_chat_stream();
    }).fail(function (xhr) {
        if (xhr.status === 401 && !prompted_error) {
            prompted_error = true;
            alert("로그인 해야 합니다.");
            window.location.href = "/login?redirect=/chat";
        }
        if (xhr.status === 504) {
            // gateway timeout
            get_newer_chat(true);
            wait_for_chat_stream();
        } else {
            // any other error
            setTimeout(function () {
                get_newer_chat(true);
                wait_for_chat_stream();
            }, 10000);
        }
    });
};
