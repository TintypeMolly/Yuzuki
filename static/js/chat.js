var KEY_CODES = {
    UP_ARROW: 38,
    DOWN_ARROW: 40
};

var slice_object = function (object, keys) {
    var sliced = {};
    for (var i in keys) {
        var field = keys[i];
        if (object.hasOwnProperty(field)) {
            sliced[field] = object[field];
        }
    }
    return sliced;
};

var chat_app = (function () {
    var format_date = function (js_date) {
        var year = js_date.getFullYear() % 1000;
        var month = js_date.getMonth();
        month += 1;
        month = month < 10 ? "0" + month : month;
        var date = js_date.getDate();
        date = date < 10 ? "0" + date : date;
        var hour = js_date.getHours();
        hour = hour < 10 ? "0" + hour : hour;
        var minute = js_date.getMinutes();
        minute = minute < 10 ? "0" + minute : minute;
        var second = js_date.getSeconds();
        second = second < 10 ? "0" + second : second;
        var formatted = year + "-" + month + "-" + date + " " + hour + ":" + minute + ":" + second;

        return formatted;
    };

    var chat_histories = {
        init: function (app, params) {
            params = params || {};

            this.app = app;
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
        init: function (app, params) {
            this.app = app;
            this.element = $("#chat-input");
            this.chat_histories = chat_histories.init();

            var mentionable_users = params["mentionable_users"] || [];
            mentionable_users.unshift("전체");

            this.element.textcomplete([
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

            this.element.on("keydown", $.proxy(this.on_keydown, this));

            return this;
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
            var chat_input_with_submit = this.element.parent();
            if (show) {
                chat_input_with_submit.show()
            } else {
                chat_input_with_submit.hide();
            }
        },
        get_text: function () {
            return this.element.val();
        },
        set_text: function (text) {
            this.element.val(text)
        },
        finalize: function () {
            this.chat_histories.add(this.get_text());
            this.chat_histories.reset();
            this.set_text("");
        }
    };

    var chat_pagination = {
        init: function (app, params) {
            this.app = app;
            this.page_total = params["page_total"] || 1;
            this.current_page = params["current_page"] || 1;
            this.max_visible = params["max_visible"] || 10;
            this.leaps = params["leaps"] || false;
            this.element = $("#pagination");

            this.element.bootpag({
                total: this.page_total,
                page: this.current_page,
                maxVisible: this.max_visible,
                leaps: this.leaps,
                renderNew: true
            }).on({
                page: $.proxy(this.load_chat_items, this)
            });

            this.element.trigger("page", this.current_page);

            return this;
        },
        load_chat_items: function (e, page) {
            $.ajax("/chat/message/data", {
                data: {page: page},
                dataType: "json"
            }).done(function (data) {
                this.change_page(page);
                this.app.process_chat_items(data);
            }.bind(this));
        },
        change_page: function (page) {
            this.current_page = page;
            this.app.chat_input_box.display_chat_input(page === 1);
        }
    };

    var chat_item = function (params) {
        this.uid = params["uid"];
        this.chat_item_class = params["chat_item_class"] || "";
        this.user_chat_color = params["user_chat_color"] || "000000";
        this.user_nickname = params["user_nickname"] || "";
        this.user_id = params["user_id"];
        this.content = params["content"] || "";
        this.created_at = params["created_at"] || "";
        this.element = $("#chat-" + this.uid);

        if (this.contain_notification()) {
            this.chat_item_class += "chat-noti";
        }
    };

    chat_item.prototype = {
        constructor: chat_item,
        to_element: function () {
            var item = $("<li>", {
                id: "chat-" + this.uid,
                class: "chat-item row " + this.chat_item_class,
                css: {
                    color: "#" + this.user_chat_color
                }
            }).append(
                $("<div>", {
                    class: "chat-item-user-nickname col-xs-2",
                    text: this.user_nickname,
                    on: { click: function (e) { open_user_popup(this.user_id); }.bind(this) }
                })
            ).append(
                $("<div>", {
                    class: "chat-content-datetime col-xs-10"
                }).append(
                    $("<span>", {
                        class: "chat-content",
                        text: this.content
                    })
                ).append(
                    $("<span>", {
                        class: "chat-datetime",
                        text: this.created_at
                    })
                )
            );

            return item;
        },
        contain_notification: function () {
            return this.content.split(" ").some(function (content) {
                return content === "@" + this.user_nickname || content === "@전체";
            });
        }
    }

    var chat_item_list = {
        init: function (app, params) {
            this.app = app;
            this.element = $("#chat-message-ul");
            this.chat_per_page = params["chat_per_page"] || 20;

            return this;
        },
        append: function (item) {
            this.element.append(item.to_element());
            if (this.element.children().length > this.chat_per_page) {
                this.element.children().first().remove();
            }
        }
    }


    var chat_form = {
        init: function (app, params) {
            this.app = app;
            this.element = $("#chat-form");
            this.submit_lock = false;
            this.element.on('submit', $.proxy(this.on_submit, this));
        },
        on_submit: function (e) {
            e.preventDefault();

            if (!this.submit_lock) {
                this.submit_lock = true;
                $.ajax("/chat/message/stream", {
                    method: "POST",
                    data: this.element.serialize(),
                    success: $.proxy(this.on_success, this),
                    error: $.proxy(this.on_error, this)
                });
            }
            return false;
        },
        on_success: function () {
            this.app.chat_input_box.finalize();
            this.submit_lock = false;
        },
        on_error: function (xhr) {
            var item = new chat_item({
                user_nickname: "system",
                content: xhr.responseText,
                chat_item_class: "chat-system",
                created_at: format_date(new Date())
            });
            this.app.chat_item_list.append(item);
            this.submit_lock = false;
        }
    }

    var chat_app = {
        init: function (params) {
            this.chat_input_box = chat_input_box.init(this,
                slice_object(params, ["mentionable_users"]));
            this.chat_histories = chat_histories.init(this);
            this.chat_pagination = chat_pagination.init(this,
                slice_object(params, ["page_total", "current_page", "max_visible", "leaps"]));
            this.chat_item_list = chat_item_list.init(this,
                slice_object(params, ["chat_per_page"]));
            this.chat_form = chat_form.init(this);

            this.latest_uid = 1;

            this.wait_for_chat_stream();
        },
        process_chat_items: function (data, enable_noti) {
            for (var i = 0; i < data.length; i++) {
                this.latest_uid = Math.max(this.latest_uid, data[i].uid);
                var chat_data = data[i];
                var item = new chat_item(chat_data);

                console.log(enable_noti, item.contain_notification());
                if (item.contain_notification() && enable_noti) {
                    this.notify_user(item);
                }

                this.chat_item_list.append(item);
            }
        },
        get_newer_chat: function (enable_noti) {
            var app = this;

            if (app.chat_pagination.current_page != 1) {
                return;
            }

            return $.ajax("/chat/message/data?id=" + this.latest_uid, {
                dataType: "json"
            }).done(function (data) {
                app.process_chat_items(data, enable_noti);
            });
        },
        wait_for_chat_stream: function () {
            var app = this;

            $.ajax("/chat/message/stream", {
                cache: false
            }).done(function () {
                app.get_newer_chat(true);
                app.wait_for_chat_stream();
            }).fail(function (xhr) {
                if (xhr.status === 401 && !prompted_error) {
                    prompted_error = true;
                    alert("로그인 해야 합니다.");
                    window.location.href = "/login?redirect=/chat";
                }
                if (xhr.status === 504) {
                    // gateway timeout
                    app.get_newer_chat(true);
                    app.wait_for_chat_stream();
                } else {
                    // any other error
                    setTimeout(function () {
                        app.get_newer_chat(true);
                        app.wait_for_chat_stream();
                    }, 10000);
                }
            });
        },
        notify_user: function (item) {
            var strip_content = $("<div>").html(item.content).text();
            var options = {
                body: strip_content,
                icon: "/favicon.ico"
            };
            if (Notification.permission === "granted" &&
                item.user_nickname !== user_nickname) {
                var notification = new Notification(item.user_nickname, options);
                notification.onclick = function () {
                    window.focus();
                    item.element.effect("highlight", 1500);
                };
            }
        }
    };

    return chat_app;
})();