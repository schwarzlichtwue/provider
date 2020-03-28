class ShellTree(dict):

    def add_shell(self, shell_obj):
        self[shell_obj.id] = shell_obj
        if shell_obj.quoted_status_id is not None:
            if shell_obj.quoted_status_id in self:
                quoted_status = self[shell_obj.quoted_status_id]
                shell_obj.quoting = quoted_status
                if shell_obj not in quoted_status.quoted_by_statuses:
                    quoted_status.quoted_by_statuses += [shell_obj]
        if shell_obj.reply_to_status_id is not None:
            if shell_obj.reply_to_status_id in self:
                reply_status = self[shell_obj.reply_to_status_id]
                shell_obj.reply_to_status = reply_status
                if shell_obj not in reply_status.replied_by_statuses:
                    reply_status.replied_by_statuses += [shell_obj]


    def filter_by_user_id(self, user_id: str):
        return ShellTree(
            {k: v for k, v in self.items() if str(v.user_id) == user_id }
        )

    def filter_by_has_root(self):
        """
        Only tweets where the parent status EXISTS (indicating the parent
        status is from the author as well)
        """
        return ShellTree(
            {k: v for k, v in self.items() if not v.reply_to_status_id or v.reply_to_status }
        )

    def filter_by_root_status_user_id(self, user_id: str):
        """
        Only tweets where the root status AND the parent status have the
        user_id
        """
        return ShellTree(
            {k: v for k, v in self.items() if not v.reply_to_status_id or
                (v.reply_to_status and str(v.reply_to_status.user_id) == user_id and str(v.status_reply_root().user_id) == user_id)})

    def filter_for_roots(self):
        return ShellTree(
            {k: v for k, v in self.items() if v.reply_to_status is None }
        )

    def filter_by_min_tweet_id(self, min_tweet_id: int):
        return ShellTree(
            {k: v for k, v in self.items() if v.id > min_tweet_id }
        )
