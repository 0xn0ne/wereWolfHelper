import re
import time
from typing import Union, List, Dict, Any

from graphviz import Digraph, backend
from graphviz import Source

ROLES = ['狼人', '恶魔', '白狼王', '平民', '警长', '预言家', '猎人', '女巫', '白痴', '守卫', '训熊师', '长老', '圣骑士', '魔术师', '丘比特', '跳神']
EXT_ROLES = ['警长']

DEAD_TYPE = ['vote', 'kill', 'poison', 'unknow']


# todo: 记录女巫施毒对象
# todo: 记录猎人攻击对象
# todo: 添加金水银水记录
class WereWolfHelper:
    min_num = 4
    max_num = 12

    def __init__(self, player_number: int):
        self.roles: List[Dict[str, str]] = []
        self.votes: List[List[List[str]]] = []
        self.deads: List[Dict[str, str]] = []
        self.current_rounds: int = 1
        self.index_round: int = 0
        self.player_number = player_number
        roles = {}
        for idx in range(self.player_number):
            roles[hex(idx + 1)] = 'player {}'.format(idx + 1)
        self.roles.append(roles)
        self.votes.append([])
        self.deads.append({})

    @classmethod
    def input_player_number(cls) -> int:
        while True:
            player_number = input('how many players: ').strip()
            try:
                player_number = int(player_number)
                if not cls.min_num <= player_number <= cls.max_num:
                    print('[-] the number of players must be min {}, and max {}'.format(cls.min_num, cls.max_num))
                    continue
                return player_number
            except ValueError:
                print('[-] error, not a number.')

    @classmethod
    def fill_display_length(cls, content: Any, length: int, front=True, fill: str = ' '):
        if type(content) != str:
            content = str(content)
        i_utf8_len = len(content.encode('utf-8'))
        i_real_len = len(content)
        if i_utf8_len != i_real_len:
            i_dis_len = (i_utf8_len + i_real_len) // 2
        else:
            i_dis_len = i_real_len
        if i_dis_len > length:
            return content

        fill_content = fill * (length - i_dis_len)
        if front:
            return fill_content + content
        return content + fill_content

    def print_choice(self, choices: List):
        half_length = len(choices) // 2
        for i in range(half_length):
            print('| {} - {} | {} - {} |'.format(self.fill_display_length(choices[i], 8, False),
                                                 self.fill_display_length(i, 2, False),
                                                 self.fill_display_length(choices[i + half_length], 8, False),
                                                 self.fill_display_length((i + half_length), 2, False)))
        if len(choices) % 2 == 1:
            print('| {} - {} |'.format(self.fill_display_length(choices[len(choices) - 1], 8, False),
                                       self.fill_display_length(len(choices) - 1, 2, False)))

    def start(self):
        if not self.player_number:
            print('[-] number of players not set')
            return
        print('the number of rounds of voting results will be updated every time the voting results are entered.')
        while True:
            print()
            print('round [{}], mode number:'.format(self.current_rounds))
            print('d - deads log')
            print('v - votes log')
            print('r - roles set')
            print('n - next round')
            print('a - all result show')
            print('c - choice result show')
            print('s - save graph')
            print('q - quit')
            mode = input('choice mode: ').strip()
            if not mode:
                if self.input_ensure_exit('game'):
                    break
                continue
            if 'deads'.startswith(mode):
                self.input_deads()
            elif 'votes'.startswith(mode):
                self.input_votes()
            elif 'roles'.startswith(mode):
                self.input_roles()
            elif 'next'.startswith(mode):
                self.next_round()
            elif 'all'.startswith(mode):
                self.draw()
            elif 'choice'.startswith(mode):
                print('[-] function not implemented')
            elif 'save'.startswith(mode):
                self.save()
            elif 'quit'.startswith(mode):
                break
            else:
                if self.input_ensure_exit('game'):
                    break

    def next_round(self):
        print('[+] next round')
        self.current_rounds += 1
        self.index_round += 1
        self.roles.append(self.roles[-1].copy())
        self.votes.append([])
        self.deads.append(self.deads[-1].copy())

    def is_valid_input_choice(self, ipt: str, min_num: int, max_num: int = None, choice: List = None) -> Union[
        int, None, bool]:
        if not ipt:
            if self.input_ensure_exit():
                return None
        if not min_num and not choice:
            raise ValueError()
        max_num = len(choice) if choice else max_num + 1
        try:
            ipt = int(ipt)
            if not min_num <= ipt < max_num:
                print('[-] the choice id must be min {}, and max {}'.format(min_num, max_num - 1))
                return False
        except ValueError:
            print('[-] error, not a number.')
            return False
        return ipt

    def is_muti_valid_input_choice(self, ipt: str, choice: List, min_num: int = 0, max_num: int = None) -> Union[
        List, None, bool]:
        r_ipt = re.findall('(\d+).+?(\d+)', ipt)
        if not r_ipt:
            return None

        max_num = max_num if max_num else len(choice) - 1
        result = []
        for idx in range(len(r_ipt)):
            src = int(r_ipt[idx][0])
            dst = int(r_ipt[idx][1])
            if not 1 <= src <= self.player_number:
                print('[-] the players id must be min {}, and max {}'.format(1, self.player_number))
                return False
            if not min_num <= dst <= max_num:
                print('[-] the choice id must be min {}, and max {}'.format(min_num, max_num))
                return False
            result.append([src, dst])
        return result

    @classmethod
    def input_ensure_exit(cls, ext_msg: Union[str, List[str]] = None) -> bool:
        l_ext_msg = ['[!]']
        if not ext_msg:
            pass
        elif type(ext_msg) == str:
            l_ext_msg.append(ext_msg)
        else:
            l_ext_msg.extend(ext_msg)
        l_ext_msg.append('finish? [Y/n]: ')
        res = input(' '.join(l_ext_msg)).strip()
        if not res or res.lower() not in 'no':
            return True
        return False

    def input_deads(self) -> Dict[str, str]:
        print()
        print('[!] next, exit without input!')
        while True:
            self.print_choice(DEAD_TYPE)
            ipt = input('witch players dead: ').strip()
            # player_id = self.is_valid_input_choice(player_id, 1, 12)
            # if player_id == None:
            #     break
            # elif player_id == False:
            #     continue
            #
            # self.print_choice(DEAD_TYPE)
            # dead_type_id = input('how did he die: ').strip()
            # dead_type_id = self.is_valid_input_choice(dead_type_id, 0, choice=DEAD_TYPE)
            # if dead_type_id == None:
            #     break
            # elif dead_type_id == False:
            #     continue

            result = self.is_muti_valid_input_choice(ipt, DEAD_TYPE)
            if result == None:
                break
            elif result == False:
                continue
            for item in result:
                self.deads[self.index_round][hex(item[0])] = DEAD_TYPE[item[1]]
        return self.deads[self.index_round]

    def input_votes(self):
        print()
        print('[!] next, exit without input!')
        votes_kill = [0 for i in range(self.player_number)]
        while True:
            ipt = input('who votes for who? (eg. 1 2 ; 3 4) ').strip()
            result = self.is_muti_valid_input_choice(ipt, [i + 1 for i in range(self.player_number)])
            if result == None:
                break
            elif result == False:
                continue
            for item in result:
                votes_kill[item[1] - 1] += 1
                self.votes[self.index_round].append([hex(item[0]), hex(item[1])])
            if self.input_ensure_exit('votes mode'):
                break
        max_dst = {}
        for i, vote_number in enumerate(votes_kill):
            if vote_number != 0:
                if vote_number not in max_dst:
                    max_dst[vote_number] = [i + 1]
                else:
                    max_dst[vote_number].append(i + 1)
        kill_result = max_dst[max(list(max_dst.keys()))]
        if len(kill_result) == 1:
            if not input('[?] is the player an idiot role [N/y]').strip().startswith('yes'):
                self.deads[self.index_round][hex(kill_result[0])] = 'vote'
        return self.votes[self.index_round]

    def input_roles(self):
        print()
        print('[!] next, exit without input!')
        while True:
            print('[*] roles id:')
            self.print_choice(ROLES)
            ipt = input('players role? (eg. 1 4; 2 7): ').strip()
            result = self.is_muti_valid_input_choice(ipt, ROLES)
            if result == None:
                break
            elif result == False:
                continue

            # player_id = self.is_valid_input_choice(player_id, 1, 12)
            # if player_id == None:
            #     break
            # elif player_id == False:
            #     continue
            #
            # self.print_choice(ROLES)
            # role_id = input('which role: ').strip()
            # role_id = self.is_valid_input_choice(role_id, 0, choice=ROLES)
            # if role_id == None:
            #     break
            # elif role_id == False:
            #     continue

            for item in result:
                player_id = item[0]
                role_id = item[1]
                for ext_role in EXT_ROLES:
                    if ext_role in self.roles[self.index_round][hex(player_id)] and ext_role != ROLES[role_id]:
                        self.roles[self.index_round][hex(player_id)] = ' '.join(
                            [ext_role, ROLES[role_id], str(player_id)])
                    else:
                        self.roles[self.index_round][hex(player_id)] = ' '.join([ROLES[role_id], str(player_id)])
        print(100001, self.roles)
        return self.roles[self.index_round]

    def draw(self, rounds_number: List[int] = None, is_show: bool = True) -> Digraph:
        dot = Digraph(comment='The Map', format='jpg', encoding='utf-8', node_attr={'fontname': 'FangSong'},
                      edge_attr={'fontname': 'FangSong'})
        if rounds_number:
            draw_rounds = rounds_number
        else:
            draw_rounds = range(self.current_rounds)
        for round_number in draw_rounds:
            for player_id in self.roles[round_number]:
                if player_id in self.deads[round_number]:
                    dot.node(player_id, ' '.join([self.roles[round_number][player_id],
                                                  'be {} in {}'.format(self.deads[round_number][player_id],
                                                                       round_number)]))
                else:
                    dot.node(player_id, self.roles[round_number][player_id])
            for vote in self.votes[round_number]:
                dot.edge(vote[0], vote[1], label=str(round_number + 1))
        try:
            if is_show:
                dot.view()
        except backend.ExecutableNotFound:
            print('please install graphviz frist. link: https://graphviz.gitlab.io/download/')
        return dot

    def save(self):
        self.draw(is_show=False).save(f'res_{time.strftime("%Y%m%d_%H.%M.%S", time.localtime(time.time()))}.jpg')


# def draw(player_number: int = 12):
#     history = {1: {'roles': {}, 'votes': [], 'deads': []}}
#     dot = Digraph(comment='The Map', format='jpg', encoding='utf-8', node_attr={'fontname': 'FangSong'},
#                   edge_attr={'fontname': 'FangSong'})
#     for idx in range(player_number):
#         history[1]['roles'][hex(idx + 1)] = 'player {}'.format(idx + 1)
#         dot.node(hex(idx + 1), 'player {}'.format(idx + 1))
#
#     print('the number of rounds of voting results will be updated every time the voting results are entered.')
#     rounds = 1
#     while True:
#         if rounds not in history:
#             history[rounds] = {'roles': history[list(history.keys())[-1]]['roles'],
#                                'votes': [], 'deads': history[list(history.keys())[-1]]['deads']}
#         print()
#         print('round {}, mode number:'.format(rounds))
#         print('d - enter deads log')
#         print('v - enter votes log')
#         print('r - enter set roles')
#         mode = input('choice mode: ')
#         if mode and mode in 'deads':
#             pass
#         elif mode and mode in 'votes':
#             history[rounds]['votes'] = input_votes(player_number)
#             for players in history[rounds]['votes']:
#                 dot.edge(players[0], players[1])
#             rounds += 1
#         elif mode and mode in 'roles':
#             history[rounds]['roles'].update(input_roles(player_number))
#             for player_id in history[rounds]['roles']:
#                 dot.node(player_id, history[rounds]['roles'][player_id])
#         else:
#             if input_ensure_exit('game'):
#                 break
#             continue
#         try:
#             dot.view()
#         except backend.ExecutableNotFound:
#             print('please install graphviz frist. link: https://graphviz.gitlab.io/download/')


def main(player_number: int = None):
    if not player_number:
        player_number = WereWolfHelper.input_player_number()
    wwh = WereWolfHelper(player_number)
    wwh.start()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--number', type=int, help='player number')
    args = parser.parse_args()
    main(args.number)
